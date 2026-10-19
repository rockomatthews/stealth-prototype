#include "SPDiagnostics.h"
#include "Prototype.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Engine/DamageEvents.h"
#include "Components/SkeletalMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

FString USPDiagnostics::RuntimeReport()
{
    TSharedRef<FJsonObject> Result=MakeShared<FJsonObject>();TArray<TSharedPtr<FJsonValue>> Worlds;
    if (GEngine) for (const FWorldContext& C:GEngine->GetWorldContexts())
    {
        UWorld* W=C.World();if (!W || !W->IsGameWorld()) continue;
        const ASPGameState* GS=W->GetGameState<ASPGameState>();if (!GS) continue;
        TSharedRef<FJsonObject> World=MakeShared<FJsonObject>();World->SetNumberField(TEXT("pie"),C.PIEInstance);
        World->SetNumberField(TEXT("netMode"),W->GetNetMode());World->SetBoolField(TEXT("practice"),GS->bPractice);
        World->SetNumberField(TEXT("phase"),static_cast<int32>(GS->Phase));World->SetNumberField(TEXT("hack"),GS->HackProgress);
        World->SetNumberField(TEXT("seconds"),GS->RoundSeconds);World->SetNumberField(TEXT("spies"),GS->Spies);World->SetNumberField(TEXT("mercs"),GS->Mercs);
        TArray<TSharedPtr<FJsonValue>> Pawns;
        for (TActorIterator<ASPCharacter> It(W);It;++It)
        {
            TSharedRef<FJsonObject> P=MakeShared<FJsonObject>();P->SetStringField(TEXT("name"),It->GetName());
            const ASPPlayerState* PS=It->GetPlayerState<ASPPlayerState>();P->SetNumberField(TEXT("playerId"),PS?PS->GetPlayerId():-1);
            P->SetBoolField(TEXT("spy"),It->IsSpy());P->SetBoolField(TEXT("local"),It->IsLocallyControlled());P->SetNumberField(TEXT("health"),It->Health);
            P->SetNumberField(TEXT("traversal"),static_cast<int32>(It->Traversal()->Motion.State));
            P->SetNumberField(TEXT("motionDuration"),It->Traversal()->Motion.Duration);
            const FVector L=It->GetActorLocation();P->SetNumberField(TEXT("x"),L.X);P->SetNumberField(TEXT("y"),L.Y);P->SetNumberField(TEXT("z"),L.Z);
            P->SetBoolField(TEXT("mesh"),It->GetMesh()->GetSkeletalMeshAsset()!=nullptr);P->SetBoolField(TEXT("crouched"),It->bIsCrouched);
            P->SetBoolField(TEXT("nightvision"),It->NightVisionEnabled());Pawns.Add(MakeShared<FJsonValueObject>(P));
        }
        World->SetArrayField(TEXT("pawns"),Pawns);Worlds.Add(MakeShared<FJsonValueObject>(World));
    }
    Result->SetArrayField(TEXT("worlds"),Worlds);Result->SetNumberField(TEXT("frameMs"),FApp::GetDeltaTime()*1000);
    FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);FJsonSerializer::Serialize(Result,Writer);return Text;
}
FString USPDiagnostics::Exercise(int32 Index,const FString& Action)
{
#if WITH_EDITOR
    if (!GEngine || Index<0 || Index>3) return TEXT("Invalid player index");
    for (const FWorldContext& C:GEngine->GetWorldContexts())
    {
        UWorld* W=C.World();if (!W || !W->IsGameWorld() || W->GetNetMode()==NM_Client) continue;
        if (!W->GetGameState<ASPGameState>()) continue;
        TArray<ASPPlayerController*> Players;
        for (FConstPlayerControllerIterator It=W->GetPlayerControllerIterator();It;++It)
            if (ASPPlayerController* PC=Cast<ASPPlayerController>(It->Get())) Players.Add(PC);
        Players.Sort([](const ASPPlayerController& A,const ASPPlayerController& B){return A.PlayerState->GetPlayerId()<B.PlayerState->GetPlayerId();});
        if (!Players.IsValidIndex(Index)) return TEXT("Player not present");
        ASPPlayerController* PC=Players[Index];ASPCharacter* Pawn=Cast<ASPCharacter>(PC->GetPawn());if (!Pawn) return TEXT("No pawn");
        if (Action==TEXT("place_ledge") || Action==TEXT("place_vault") || Action==TEXT("place_terminal") || Action==TEXT("place_open"))
        {
            Pawn->Traversal()->Drop();Pawn->UnCrouch();
            FVector L;FRotator R;
            if (Action==TEXT("place_ledge")) {L=FVector(-1050,560,90);R=FRotator(0,90,0);}
            else if (Action==TEXT("place_vault")) {L=FVector(-480,0,90);R=FRotator::ZeroRotator;}
            else if (Action==TEXT("place_terminal")) {L=FVector(-100,0,90);R=FRotator::ZeroRotator;}
            else {L=FVector(-1100,-800,90);R=FRotator::ZeroRotator;}
            Pawn->SetActorLocation(L,false,nullptr,ETeleportType::TeleportPhysics);Pawn->SetActorRotation(R);PC->SetControlRotation(R);PC->ClientSetRotation(R,true);
            Pawn->ForceNetUpdate();return TEXT("Placed for editor test");
        }
        if (Action==TEXT("expire")) {W->GetGameState<ASPGameState>()->RoundSeconds=.1f;return TEXT("Round timer shortened for test");}
        if (Action==TEXT("near_complete")) {W->GetGameState<ASPGameState>()->HackProgress=.99f;return TEXT("Hack progress set for win-condition test");}
        if (Action==TEXT("damage")) {FDamageEvent Event;Pawn->TakeDamage(100,Event,nullptr,nullptr);return TEXT("Damage applied");}
        if (Action==TEXT("network_lag")) {GEngine->Exec(W,TEXT("NetEmulation.PktLag 100"));GEngine->Exec(W,TEXT("NetEmulation.PktLoss 2"));return TEXT("100ms packet lag / 2 percent loss requested");}
        if (Action==TEXT("network_reset")) {GEngine->Exec(W,TEXT("NetEmulation.PktLag 0"));GEngine->Exec(W,TEXT("NetEmulation.PktLoss 0"));return TEXT("Network emulation reset requested");}
        const TArray<FString> Allowed={TEXT("traverse"),TEXT("drop"),TEXT("hack"),TEXT("release"),TEXT("fire"),TEXT("role"),TEXT("crouch"),TEXT("nightvision")};
        if (!Allowed.Contains(Action)) return TEXT("Unknown test action");
        PC->ClientExercise(Action);return TEXT("Owning-client input requested");
    }
#endif
    return TEXT("Editor game world not available");
}
