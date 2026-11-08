#include "SPVoiceComponent.h"
#include "Prototype.h"
#include "VoiceModule.h"
#include "Interfaces/VoiceCapture.h"
#include "Interfaces/VoiceCodec.h"
#include "Components/AudioComponent.h"
#include "Sound/SoundWaveProcedural.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Engine/Engine.h"

namespace { constexpr int32 Rate=16000,FrameBytes=640,MaxPacket=512; }

ASPPlayerController::ASPPlayerController() {Voice=CreateDefaultSubobject<USPVoiceComponent>(TEXT("PrivateVoice"));}
bool ASPPlayerController::IsAutomationInput() const
{
#if WITH_EDITOR
    return bAutomatedInput;
#else
    return false;
#endif
}
void ASPPlayerController::ServerVoiceFrame_Implementation(ESPVoiceChannel Channel,uint32 Epoch,uint32 Token,uint32 Stream,uint32 Sequence,const TArray<uint8>& Data) {Voice->Relay(Channel,Epoch,Token,Stream,Sequence,Data);}
void ASPPlayerController::ClientVoiceFrame_Implementation(int32 Sender,ESPVoiceChannel Channel,uint32 Epoch,uint32 Token,uint32 Stream,uint32 Sequence,const TArray<uint8>& Data) {Voice->Receive(Sender,Channel,Epoch,Token,Stream,Sequence,Data);}
void ASPPlayerController::ClientVoicePair_Implementation(int32 Peer,uint32 Token) {Voice->SetPair(Peer,Token);}
void ASPPlayerController::ClientVoiceEpoch_Implementation(uint32 Epoch) {Voice->ResetEpoch(Epoch);}

USPVoiceComponent::USPVoiceComponent() {PrimaryComponentTick.bCanEverTick=true;}
void USPVoiceComponent::ToggleMute() {bMicMuted=!bMicMuted;StopCapture();bSentStream=false;NextCaptureAttempt=0;}
void USPVoiceComponent::StopCapture()
{
    if (Capture) {Capture->Stop();Capture->Shutdown();Capture.Reset();}
    PendingPCM.Reset();
}
void USPVoiceComponent::ClearStream(FSPVoiceStream& S)
{
    if (S.Audio) {S.Audio->Stop();S.Audio->DestroyComponent();}
    if (S.Wave) S.Wave->ResetAudio();
    S.Audio=nullptr;S.Wave=nullptr;S.Decoder.Reset();
}
void USPVoiceComponent::SetPair(int32 Peer,uint32 Token)
{
    if (PairToken && PairToken!=Token) ClosedPairs.Add(PairToken);
    if (ClosedPairs.Num()>128) ClosedPairs.Reset();
    PairPeer=Peer;PairToken=Token;StopCapture();bSentStream=false;NextCaptureAttempt=0;
    for (auto It=Streams.CreateIterator();It;++It) if (It.Value().Channel==ESPVoiceChannel::Grab)
    {ClearStream(It.Value());It.RemoveCurrent();}
}
void USPVoiceComponent::ResetEpoch(uint32 Epoch)
{
    KnownEpoch=FMath::Max(KnownEpoch,Epoch);StopCapture();bSentStream=false;
    for (auto& Entry:Streams) ClearStream(Entry.Value);Streams.Reset();
    SetPair(-1,0);
}
bool USPVoiceComponent::MicrophoneAllowed() const
{
    const ASPPlayerController* PC=Cast<ASPPlayerController>(GetOwner());
    if (!PC || !PC->IsLocalController() || PC->IsAutomationInput()) return false;
#if WITH_EDITOR
    // One process cannot represent four independent human microphones. Use standalone
    // instances on separate Macs for real speech; multi-PIE uses encoded test tones.
    if (GetWorld()->WorldType==EWorldType::PIE && GEngine)
    {
        int32 Games=0;for (const FWorldContext& C:GEngine->GetWorldContexts()) if (C.World() && C.World()->IsGameWorld()) ++Games;
        if (Games>1) return false;
    }
#endif
    return true;
}
void USPVoiceComponent::Encode(ESPVoiceChannel Channel,uint32 Epoch,uint32 Token,const uint8* PCM)
{
    ASPPlayerController* PC=CastChecked<ASPPlayerController>(GetOwner());
    if (bMicMuted) return;
    if (!Encoder) Encoder=FVoiceModule::Get().CreateVoiceEncoder(Rate,1,EAudioEncodeHint::VoiceEncode_Voice);
    if (!Encoder) {CaptureStatus=TEXT("Voice codec unavailable");return;}
    if (!bSentStream || Channel!=TransmitChannel || Token!=TransmitToken || GetWorld()->GetTimeSeconds()-LastTransmit>.3)
    {Encoder->Reset();++StreamId;TransmitChannel=Channel;TransmitToken=Token;bSentStream=true;}
    TArray<uint8> Packet;Packet.SetNumUninitialized(MaxPacket);uint32 Size=MaxPacket;
    const int32 Remainder=Encoder->Encode(PCM,FrameBytes,Packet.GetData(),Size);
    if (Remainder!=0 || Size==0 || Size>MaxPacket) return;
    Packet.SetNum(Size);++SequenceId;++Sent;LastTransmit=GetWorld()->GetTimeSeconds();
    PC->ServerVoiceFrame(Channel,Epoch,Token,StreamId,SequenceId,Packet);
}
void USPVoiceComponent::TickComponent(float Delta,ELevelTick TickType,FActorComponentTickFunction* Function)
{
    Super::TickComponent(Delta,TickType,Function);
    ASPPlayerController* PC=Cast<ASPPlayerController>(GetOwner());if (!PC || !PC->IsLocalController()) return;
    const ASPGameState* GS=GetWorld()->GetGameState<ASPGameState>();if (!GS) return;
    if (GS->VoiceEpoch>KnownEpoch) ResetEpoch(GS->VoiceEpoch);
    for (auto It=Streams.CreateIterator();It;++It)
        if (GetWorld()->GetTimeSeconds()-It.Value().ReceivedAt>.35 || (It.Value().Channel==ESPVoiceChannel::Grab && (PairToken!=It.Value().Token || !PairToken)))
        {ClearStream(It.Value());It.RemoveCurrent();}
    const ASPPlayerState* PS=PC->GetPlayerState<ASPPlayerState>();
    const bool TeamPresent=PS && (PS->Team==ESPTeam::Spy?GS->Spies:GS->Mercs)>1;
    const ESPVoiceChannel Desired=DesiredChannel();
    const bool Ready=!bMicMuted && (Desired==ESPVoiceChannel::Grab || (bOpenTeamMic && TeamPresent));
    if (!Ready || !MicrophoneAllowed())
    {
        StopCapture();bSentStream=false;
        CaptureStatus=bMicMuted?TEXT("Mic muted"):(!MicrophoneAllowed()?TEXT("Mic off in automated/multi-client PIE"):TEXT("Waiting for voice partner"));return;
    }
    if (bSentStream && (Desired!=TransmitChannel || (Desired==ESPVoiceChannel::Grab && PairToken!=TransmitToken))) {StopCapture();bSentStream=false;}
    if (!Capture)
    {
        if (GetWorld()->GetTimeSeconds()<NextCaptureAttempt) return;
        NextCaptureAttempt=GetWorld()->GetTimeSeconds()+2.;
        Capture=FVoiceModule::Get().CreateVoiceCapture(TEXT(""),Rate,1);
        if (!Capture) {CaptureStatus=TEXT("Microphone unavailable: check macOS permission/device");return;}
    }
    if (!Capture->IsCapturing() && !Capture->Start()) {CaptureStatus=TEXT("Microphone could not start");Capture.Reset();return;}
    CaptureStatus=Desired==ESPVoiceChannel::Grab?TEXT("Grab microphone live"):TEXT("Team microphone live");
    uint32 Available=0;const EVoiceCaptureState::Type State=Capture->GetCaptureState(Available);
    if (State==EVoiceCaptureState::Error || State==EVoiceCaptureState::UnInitialized)
    {StopCapture();CaptureStatus=TEXT("Microphone disconnected; retrying");return;}
    if (State!=EVoiceCaptureState::Ok || !Available) return;
    if (Available>Rate*2) {StopCapture();return;}
    TArray<uint8> PCM;PCM.SetNumUninitialized(Available);uint32 Bytes=0;
    uint64 SampleCounter=0;
    const EVoiceCaptureState::Type ReadState=Capture->GetVoiceData(PCM.GetData(),Available,Bytes,SampleCounter);
    if (ReadState!=EVoiceCaptureState::Ok || !Bytes || Bytes>Available) return;
    PendingPCM.Append(PCM.GetData(),Bytes);
    // Bound latency after a slow frame instead of streaming old speech later.
    if (PendingPCM.Num()>FrameBytes*5) PendingPCM.RemoveAt(0,PendingPCM.Num()-FrameBytes*5,EAllowShrinking::No);
    int32 Used=0;
    while (PendingPCM.Num()-Used>=FrameBytes) {Encode(Desired,KnownEpoch,Desired==ESPVoiceChannel::Grab?PairToken:0,PendingPCM.GetData()+Used);Used+=FrameBytes;}
    if (Used) PendingPCM.RemoveAt(0,Used,EAllowShrinking::No);
}
void USPVoiceComponent::Relay(ESPVoiceChannel Channel,uint32 Epoch,uint32 Token,uint32 Stream,uint32 Sequence,const TArray<uint8>& Data)
{
    ASPPlayerController* Sender=CastChecked<ASPPlayerController>(GetOwner());
    const ASPGameState* GS=GetWorld()->GetGameState<ASPGameState>();
    const ASPPlayerState* PS=Sender->GetPlayerState<ASPPlayerState>();
    const double Now=GetWorld()->GetTimeSeconds();if (Now-RateStart>=1) {RateStart=Now;RateCount=0;}
    if (!GetOwner()->HasAuthority() || !GS || !PS || Epoch!=GS->VoiceEpoch || Data.IsEmpty() || Data.Num()>MaxPacket || Sequence<=ServerSequence || ++RateCount>65 || (Channel!=ESPVoiceChannel::Team && Channel!=ESPVoiceChannel::Grab)) {++Rejected;return;}
    ServerSequence=Sequence;
    if (Channel==ESPVoiceChannel::Grab)
    {
        const ASPCharacter* P=Cast<ASPCharacter>(Sender->GetPawn());
        const ASPCharacter* Peer=P?P->Grab.Partner.Get():nullptr;
        if (!P || !IsValid(Peer) || !P->IsRoundActive() || !Peer->IsRoundActive() || P->Grab.Token!=Token || !Token || Peer->Grab.Partner!=P || Peer->Grab.Token!=Token || (P->IsCaptor()?P->IsStunned():Peer->IsStunned()) || FVector::DistSquared(P->GetActorLocation(),Peer->GetActorLocation())>FMath::Square(P->IsFinishing()?260.f:180.f)) {++Rejected;return;}
        if (ASPPlayerController* Target=Cast<ASPPlayerController>(Peer->GetController())) Target->ClientVoiceFrame(PS->GetPlayerId(),Channel,Epoch,Token,Stream,Sequence,Data);
        return;
    }
    const ASPCharacter* Pawn=Cast<ASPCharacter>(Sender->GetPawn());
    if (Token!=0 || (Pawn && Pawn->IsRestrained())) {++Rejected;return;}
    // Never broadcast enemy audio and then rely on a client-side mute.
    for (FConstPlayerControllerIterator It=GetWorld()->GetPlayerControllerIterator();It;++It)
        if (ASPPlayerController* Target=Cast<ASPPlayerController>(It->Get()))
            if (Target!=Sender) if (const ASPPlayerState* Other=Target->GetPlayerState<ASPPlayerState>())
                if (Other->Team==PS->Team) Target->ClientVoiceFrame(PS->GetPlayerId(),Channel,Epoch,0,Stream,Sequence,Data);
}
void USPVoiceComponent::Receive(int32 Sender,ESPVoiceChannel Channel,uint32 Epoch,uint32 Token,uint32 Stream,uint32 Sequence,const TArray<uint8>& Data)
{
    ++RawReceived;++RawFrom.FindOrAdd(Sender);
    const ASPGameState* GS=GetWorld()->GetGameState<ASPGameState>();
    if (!GS || Epoch!=FMath::Max(KnownEpoch,GS->VoiceEpoch) || Data.IsEmpty() || Data.Num()>MaxPacket) return;
    if (Channel==ESPVoiceChannel::Grab && (!Token || ClosedPairs.Contains(Token) || PairToken!=Token || PairPeer!=Sender)) return;
    const int32 Key=Sender*2+static_cast<int32>(Channel);
    if (Sequence<=LastReceivedSequence.FindRef(Key)) return;
    FSPVoiceStream& S=Streams.FindOrAdd(Key);
    if (S.Wave && (S.Stream!=Stream || S.Token!=Token || S.Epoch!=Epoch)) ClearStream(S);
    if (S.Decoder && Sequence<=S.Sequence) return;
    if (!S.Decoder) S.Decoder=FVoiceModule::Get().CreateVoiceDecoder(Rate,1);
    if (!S.Decoder) return;
    uint8 PCM[4096];uint32 Bytes=sizeof(PCM);S.Decoder->Decode(Data.GetData(),Data.Num(),PCM,Bytes);
    if (!Bytes || Bytes>sizeof(PCM) || Bytes%2) return;
    if (!S.Wave)
    {
        S.Wave=NewObject<USoundWaveProcedural>(this);S.Wave->SetSampleRate(Rate);S.Wave->NumChannels=1;
        S.Wave->SoundGroup=SOUNDGROUP_Voice;S.Wave->Duration=INDEFINITELY_LOOPING_DURATION;
        S.Audio=NewObject<UAudioComponent>(GetOwner());S.Audio->bAutoActivate=false;S.Audio->bAllowSpatialization=false;S.Audio->bIsUISound=true;
        S.Audio->RegisterComponentWithWorld(GetWorld());S.Audio->SetSound(S.Wave);S.Audio->Play();if (S.Audio->IsPlaying()) ++AudioStarts;
    }
    if (S.Wave->GetAvailableAudioByteCount()>Rate/2) S.Wave->ResetAudio();
    S.Wave->QueueAudio(PCM,Bytes);S.Epoch=Epoch;S.Token=Token;S.Stream=Stream;S.Sequence=Sequence;S.Channel=Channel;S.ReceivedAt=GetWorld()->GetTimeSeconds();
    LastReceivedSequence.Add(Key,Sequence);
    ++Received;++ReceivedFrom.FindOrAdd(Sender);DecodedBytes+=Bytes;LastReceive=S.ReceivedAt;
    for (uint32 I=0;I<Bytes;I+=2) if (PCM[I] || PCM[I+1]) ++NonzeroSamples;
}
FString USPVoiceComponent::HUD() const
{
    if (bMicMuted) return TEXT("VOICE MUTED | View / M unmute");
    const FString Route=DesiredChannel()==ESPVoiceChannel::Grab?TEXT("GRAB OPEN MIC"):TEXT("TEAM OPEN MIC");
    return FString::Printf(TEXT("VOICE %s | View / M mute | %s%s"),*Route,*CaptureStatus,GetWorld()->GetTimeSeconds()-LastReceive<.35?TEXT(" | RECEIVING"):TEXT(""));
}
FString USPVoiceComponent::Report() const
{
    TSharedRef<FJsonObject> R=MakeShared<FJsonObject>();R->SetBoolField(TEXT("openTeamMic"),bOpenTeamMic);R->SetBoolField(TEXT("muted"),bMicMuted);
    R->SetBoolField(TEXT("automaticGrabVoice"),DesiredChannel()==ESPVoiceChannel::Grab);R->SetNumberField(TEXT("pairPeer"),PairPeer);R->SetNumberField(TEXT("pairToken"),PairToken);
    R->SetNumberField(TEXT("sent"),Sent);R->SetNumberField(TEXT("received"),Received);R->SetNumberField(TEXT("decodedBytes"),DecodedBytes);
    R->SetNumberField(TEXT("nonzeroSamples"),NonzeroSamples);R->SetNumberField(TEXT("rejected"),Rejected);R->SetNumberField(TEXT("epoch"),KnownEpoch);
    R->SetBoolField(TEXT("microphoneCapturing"),Capture && Capture->IsCapturing());R->SetStringField(TEXT("captureStatus"),CaptureStatus);R->SetStringField(TEXT("microphoneProbe"),ProbeStatus);
    R->SetNumberField(TEXT("activeStreams"),Streams.Num());R->SetNumberField(TEXT("audioStarts"),AudioStarts);R->SetStringField(TEXT("desiredChannel"),DesiredChannel()==ESPVoiceChannel::Grab?TEXT("Grab"):TEXT("Team"));
    TSharedRef<FJsonObject> From=MakeShared<FJsonObject>();for (const auto& Entry:ReceivedFrom) From->SetNumberField(FString::FromInt(Entry.Key),Entry.Value);R->SetObjectField(TEXT("from"),From);
    TSharedRef<FJsonObject> Raw=MakeShared<FJsonObject>();for (const auto& Entry:RawFrom) Raw->SetNumberField(FString::FromInt(Entry.Key),Entry.Value);R->SetObjectField(TEXT("rawFrom"),Raw);R->SetNumberField(TEXT("rawReceived"),RawReceived);
    FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);FJsonSerializer::Serialize(R,Writer);return Text;
}
void USPVoiceComponent::Synthetic(ESPVoiceChannel Channel,bool Stale)
{
#if WITH_EDITOR
    const ASPPlayerController* PC=CastChecked<ASPPlayerController>(GetOwner());if (!PC->IsAutomationInput()) return;
    int16 PCM[FrameBytes/2];for (int32 I=0;I<FrameBytes/2;++I) PCM[I]=static_cast<int16>(FMath::Sin(I*2.f*PI*440/Rate)*3000);
    for (int32 N=0;N<3;++N) Encode(Channel,(Stale && Channel==ESPVoiceChannel::Team)?KnownEpoch-1:KnownEpoch,Channel==ESPVoiceChannel::Grab?(Stale?PairToken+999:PairToken):0,reinterpret_cast<uint8*>(PCM));
#endif
}
void USPVoiceComponent::ProbeMicrophone()
{
#if WITH_EDITOR
    const ASPPlayerController* PC=Cast<ASPPlayerController>(GetOwner());
    if (!PC || !PC->IsLocalController()) return;
    // Device-open check only: never read, retain, encode or transmit microphone data.
    TSharedPtr<IVoiceCapture> Probe=FVoiceModule::Get().CreateVoiceCapture(TEXT(""),Rate,1);
    if (!Probe) {ProbeStatus=TEXT("Unavailable or permission denied");return;}
    const bool Started=Probe->Start();
    ProbeStatus=Started && Probe->IsCapturing()?TEXT("Microphone opened successfully"):TEXT("Microphone could not start");
    Probe->Stop();Probe->Shutdown();
#endif
}
void USPVoiceComponent::ResetStats() {Sent=Received=DecodedBytes=NonzeroSamples=Rejected=AudioStarts=RawReceived=0;ReceivedFrom.Reset();RawFrom.Reset();}
void USPVoiceComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    StopCapture();
    for (auto& Entry:Streams) ClearStream(Entry.Value);Streams.Reset();Super::EndPlay(Reason);
}
