#include "SPDiagnostics.h"
#include "Prototype.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/NetDriver.h"
#include "EngineUtils.h"
#include "Engine/DamageEvents.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "TimerManager.h"

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
#if DO_ENABLE_NET_TEST
        if (const UNetDriver* Driver=W->GetNetDriver())
        {World->SetNumberField(TEXT("packetLag"),Driver->PacketSimulationSettings.PktLag);World->SetNumberField(TEXT("packetLoss"),Driver->PacketSimulationSettings.PktLoss);}
#endif
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
            P->SetStringField(TEXT("meshPath"),GetPathNameSafe(It->GetMesh()->GetSkeletalMeshAsset()));
            P->SetBoolField(TEXT("appearanceView"),It->IsInspectingAppearance());
            const FTransform HeadPose=It->GetMesh()->GetSocketTransform(TEXT("head"));
            P->SetNumberField(TEXT("headBoneScale"),HeadPose.GetScale3D().GetMax());
            P->SetNumberField(TEXT("headDistance"),FVector::Dist(HeadPose.GetLocation(),It->GetActorLocation()));
            if (const UAnimSingleNodeInstance* Anim=It->GetMesh()->GetSingleNodeInstance())
                P->SetNumberField(TEXT("animationTime"),Anim->GetCurrentTime());
            P->SetBoolField(TEXT("nightvision"),It->NightVisionEnabled());Pawns.Add(MakeShared<FJsonValueObject>(P));
            P->SetBoolField(TEXT("flashlight"),It->FlashlightEnabled());P->SetBoolField(TEXT("aiming"),It->IsAiming());
            P->SetNumberField(TEXT("gogglePitch"),It->GogglePitch());P->SetNumberField(TEXT("cameraDistance"),It->CameraDistance());
            P->SetNumberField(TEXT("cameraFOV"),It->CameraFOV());
            P->SetNumberField(TEXT("actualCameraOffset"),It->ActualCameraOffset());
            P->SetNumberField(TEXT("viewYaw"),It->GetControlRotation().Yaw);P->SetNumberField(TEXT("viewPitch"),It->GetControlRotation().Pitch);
            if (const auto* PC=Cast<ASPPlayerController>(It->GetController()))
            {
                P->SetBoolField(TEXT("gamepad"),PC->UsingGamepad());P->SetStringField(TEXT("controller"),PC->GetPathName());
                if (const AHUD* HUD=PC->GetHUD())
                {P->SetStringField(TEXT("hud"),HUD->GetPathName());P->SetBoolField(TEXT("hudShown"),HUD->bShowHUD);if (const ASPHUD* H=Cast<ASPHUD>(HUD)) P->SetNumberField(TEXT("hudLastDraw"),H->LastDrawTime);}
            }
            TArray<TSharedPtr<FJsonValue>> Keys;for (const auto& Key:It->InputKeys()) Keys.Add(MakeShared<FJsonValueString>(Key));P->SetArrayField(TEXT("inputKeys"),Keys);
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
        if (Action==TEXT("automation_on") || Action==TEXT("automation_off"))
        {
            for (ASPPlayerController* Target:Players) W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(Target,[Target,Action]() {Target->ClientExercise(Action);}));
            return TEXT("Editor-only input isolation queued on all players");
        }
        if (Action==TEXT("duel_open") || Action==TEXT("duel_blocked") || Action==TEXT("takedown_front") || Action==TEXT("takedown_rear"))
        {
            if (Players.Num()!=4) return TEXT("Four players required for combat fixture");
            for (int32 Slot:{1,2})
            {
                ASPPlayerController* TargetPC=Players[Slot];ASPCharacter* Target=Cast<ASPCharacter>(TargetPC->GetPawn());
                if (!Target || Target->Health<=0) return TEXT("Combat fixture requires living players");
                const bool Merc=Slot==1;const bool Takedown=Action.StartsWith(TEXT("takedown"));
                const FVector L(Merc?(Takedown?-1000.f:(Action==TEXT("duel_open")?-700.f:-450.f)):-1100.f,Action==TEXT("duel_blocked")?-400.f:-800.f,90.f);
                const FRotator R(0,Merc && Action!=TEXT("takedown_rear")?180.f:0.f,0);
                Target->Traversal()->Drop();Target->UnCrouch();Target->SetActorLocation(L,false,nullptr,ETeleportType::TeleportPhysics);
                Target->SetActorRotation(R);TargetPC->SetControlRotation(R);Target->ForceNetUpdate();
                W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(TargetPC,[TargetPC,R]() {TargetPC->ClientSetRotation(R,true);}));
            }
            return TEXT("Combat fixture placed");
        }
        if (Action==TEXT("place_ledge") || Action==TEXT("place_vault") || Action==TEXT("place_terminal") || Action==TEXT("place_open"))
        {
            Pawn->Traversal()->Drop();Pawn->UnCrouch();
            FVector L;FRotator R;
            if (Action==TEXT("place_ledge")) {L=FVector(-1050,560,90);R=FRotator(0,90,0);}
            else if (Action==TEXT("place_vault")) {L=FVector(-480,0,90);R=FRotator::ZeroRotator;}
            else if (Action==TEXT("place_terminal")) {L=FVector(-100,0,90);R=FRotator::ZeroRotator;}
            else {L=FVector(-1100,-800,90);R=FRotator::ZeroRotator;}
            Pawn->SetActorLocation(L,false,nullptr,ETeleportType::TeleportPhysics);Pawn->SetActorRotation(R);PC->SetControlRotation(R);
            W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(PC,[PC,R]() {PC->ClientSetRotation(R,true);}));
            Pawn->ForceNetUpdate();return TEXT("Placed for editor test");
        }
        if (Action==TEXT("expire")) {W->GetGameState<ASPGameState>()->RoundSeconds=.1f;return TEXT("Round timer shortened for test");}
        if (Action==TEXT("near_complete")) {W->GetGameState<ASPGameState>()->HackProgress=.99f;return TEXT("Hack progress set for win-condition test");}
        if (Action==TEXT("damage")) {FDamageEvent Event;Pawn->TakeDamage(100,Event,nullptr,nullptr);return TEXT("Damage applied");}
        if (Action==TEXT("network_lag") || Action==TEXT("network_reset"))
        {
#if DO_ENABLE_NET_TEST
            for (const FWorldContext& Context:GEngine->GetWorldContexts()) if (UWorld* GameWorld=Context.World())
                if (GameWorld->IsGameWorld()) if (UNetDriver* Driver=GameWorld->GetNetDriver())
                {auto Settings=Driver->PacketSimulationSettings;Settings.PktLag=Action==TEXT("network_lag")?100:0;Settings.PktLoss=Action==TEXT("network_lag")?2:0;Driver->SetPacketSimulationSettings(Settings);}
            return TEXT("Network emulation settings applied; inspect runtime_report for readback");
#else
            return TEXT("Network emulation unavailable in this build");
#endif
        }
        const TArray<FString> Allowed={TEXT("traverse"),TEXT("drop"),TEXT("hack"),TEXT("release"),TEXT("fire"),TEXT("role"),TEXT("spy"),TEXT("merc"),TEXT("crouch"),TEXT("nightvision")};
        if (!Allowed.Contains(Action) && !Action.StartsWith(TEXT("pad_"))) return TEXT("Unknown test action");
        // Native MCP executes in editor context. Dispatch RPCs during the game world's
        // tick so PIE chooses the owning client's network callspace correctly.
        W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(PC,[PC,Action]() { PC->ClientExercise(Action); }));
        return TEXT("Owning-client input queued for game tick");
    }
#endif
    return TEXT("Editor game world not available");
}
