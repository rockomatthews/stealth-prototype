#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SPVoiceComponent.generated.h"
class IVoiceCapture;
class IVoiceEncoder;
class IVoiceDecoder;
class USoundWaveProcedural;
class UAudioComponent;

UENUM()
enum class ESPVoiceChannel : uint8 { Team, Grab };

USTRUCT()
struct FSPVoiceStream
{
    GENERATED_BODY()
    UPROPERTY() TObjectPtr<USoundWaveProcedural> Wave;
    UPROPERTY() TObjectPtr<UAudioComponent> Audio;
    TSharedPtr<IVoiceDecoder> Decoder;
    ESPVoiceChannel Channel=ESPVoiceChannel::Team;
    uint32 Epoch=0,Token=0,Stream=0,Sequence=0;
    double ReceivedAt=0;
};

UCLASS(ClassGroup=Audio)
class STEALTHPROTOTYPE_API USPVoiceComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    USPVoiceComponent();
    virtual void TickComponent(float Delta,ELevelTick TickType,FActorComponentTickFunction* Function) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    void ToggleMute();
    void SetPair(int32 Peer,uint32 Token);
    void ResetEpoch(uint32 Epoch);
    void Relay(ESPVoiceChannel Channel,uint32 Epoch,uint32 Token,uint32 Stream,uint32 Sequence,const TArray<uint8>& Data);
    void Receive(int32 Sender,ESPVoiceChannel Channel,uint32 Epoch,uint32 Token,uint32 Stream,uint32 Sequence,const TArray<uint8>& Data);
    FString HUD() const;
    FString Report() const;
    void Synthetic(ESPVoiceChannel Channel,bool Stale=false);
    ESPVoiceChannel DesiredChannel() const { return PairToken && PairPeer>=0?ESPVoiceChannel::Grab:ESPVoiceChannel::Team; }
    void ResetStats();
    void ProbeMicrophone();
    UPROPERTY(EditAnywhere,Category="Voice") bool bOpenTeamMic=true;
    bool bMicMuted=false;
    int32 PairPeer=-1;
    uint32 PairToken=0;
private:
    bool bSentStream=false;
    ESPVoiceChannel TransmitChannel=ESPVoiceChannel::Team;
    uint32 KnownEpoch=1,TransmitToken=0,StreamId=0,SequenceId=0;
    TSharedPtr<IVoiceCapture> Capture;
    TSharedPtr<IVoiceEncoder> Encoder;
    TArray<uint8> PendingPCM;
    UPROPERTY(Transient) TMap<int32,FSPVoiceStream> Streams;
    TSet<uint32> ClosedPairs;
    double RateStart=0;
    int32 RateCount=0;
    uint32 ServerSequence=0;
    TMap<int32,int32> ReceivedFrom;
    TMap<int32,int32> RawFrom;
    int32 RawReceived=0;
    TMap<int32,uint32> LastReceivedSequence;
    double NextCaptureAttempt=0;
    int32 Sent=0,Received=0,DecodedBytes=0,NonzeroSamples=0,Rejected=0,AudioStarts=0;
    FString CaptureStatus=TEXT("Idle");
    FString ProbeStatus=TEXT("Not checked");
    double LastTransmit=-10,LastReceive=-10;
    void StopCapture();
    void ClearStream(FSPVoiceStream& Stream);
    void Encode(ESPVoiceChannel Channel,uint32 Epoch,uint32 Token,const uint8* PCM);
    bool MicrophoneAllowed() const;
};
