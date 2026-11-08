#include "SPDiagnostics.h"
#include "Prototype.h"
#include "SPRecoveryFX.h"
#include "SPWarehouse.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/NetDriver.h"
#include "Engine/NetConnection.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "EngineUtils.h"
#include "Engine/DamageEvents.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "SPEquipmentAnimInstance.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "TimerManager.h"
#include "GameFramework/WorldSettings.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "HAL/IConsoleManager.h"

FString USPDiagnostics::RuntimeReport()
{
    TSharedRef<FJsonObject> Result=MakeShared<FJsonObject>();TArray<TSharedPtr<FJsonValue>> Worlds;
    if (GEngine) for (const FWorldContext& C:GEngine->GetWorldContexts())
    {
        UWorld* W=C.World();if (!W || !W->IsGameWorld()) continue;
        const ASPGameState* GS=W->GetGameState<ASPGameState>();if (!GS) continue;
        TSharedRef<FJsonObject> World=MakeShared<FJsonObject>();World->SetNumberField(TEXT("pie"),C.PIEInstance);
        int32 Crates=0;for (TActorIterator<ASPWarehouse> It(W);It;++It) for (const auto& Ref:It->Generated) if (const auto* Cmp=Cast<UHierarchicalInstancedStaticMeshComponent>(Ref.Get())) if (Cmp->GetStaticMesh() && Cmp->GetStaticMesh()->GetName()==TEXT("SM_Crate")) Crates+=Cmp->GetInstanceCount();
        World->SetNumberField(TEXT("crates"),Crates);
        World->SetStringField(TEXT("map"),W->GetMapName());int32 RopeCount=0,VentCount=0,DoorCount=0;bool DoorOpen=false;
        for (TActorIterator<ASPRope> It(W);It;++It) ++RopeCount;for (TActorIterator<ASPVentRoute> It(W);It;++It) ++VentCount;
        for (TActorIterator<ASPMercDoor> It(W);It;++It) {++DoorCount;DoorOpen|=It->bOpen;}
        if (RopeCount>0)
        {
            FCollisionQueryParams Q(SCENE_QUERY_STAT(VentCapsuleProbe),false);
            World->SetBoolField(TEXT("spyVentClear"),!W->OverlapBlockingTestByChannel(FVector(0,-900,824),FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(34,42),Q));
            World->SetBoolField(TEXT("mercVentBlocked"),W->OverlapBlockingTestByChannel(FVector(0,-900,842),FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(34,60),Q));
        }
        World->SetNumberField(TEXT("ropes"),RopeCount);World->SetNumberField(TEXT("vents"),VentCount);World->SetNumberField(TEXT("mercDoors"),DoorCount);World->SetBoolField(TEXT("mercDoorOpen"),DoorOpen);
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
            TSharedPtr<FJsonObject> Equipment;
            auto Reader=TJsonReaderFactory<>::Create(It->EquipmentReport());
            if (FJsonSerializer::Deserialize(Reader,Equipment)) P->SetObjectField(TEXT("equipment"),Equipment);
            const FTransform HeadPose=It->GetMesh()->GetSocketTransform(TEXT("head"));
            P->SetNumberField(TEXT("headBoneScale"),HeadPose.GetScale3D().GetMax());
            P->SetNumberField(TEXT("headDistance"),FVector::Dist(HeadPose.GetLocation(),It->GetActorLocation()));
            if (const UAnimSingleNodeInstance* Anim=It->GetMesh()->GetSingleNodeInstance())
                P->SetNumberField(TEXT("animationTime"),Anim->GetCurrentTime());
            if (const USPEquipmentAnimInstance* Anim=Cast<USPEquipmentAnimInstance>(It->GetMesh()->GetAnimInstance()))
                {P->SetNumberField(TEXT("animationTime"),Anim->LocomotionTime());P->SetStringField(TEXT("animationAsset"),GetPathNameSafe(Anim->Locomotion));}
            P->SetNumberField(TEXT("dropKnockouts"),It->DropKnockoutCount);P->SetNumberField(TEXT("verticalSpeed"),It->GetVelocity().Z);P->SetBoolField(TEXT("falling"),It->GetCharacterMovement()->IsFalling());P->SetNumberField(TEXT("recoveryGrabBlocks"),It->RecoveryGrabBlocks);P->SetNumberField(TEXT("recoveryDropBlocks"),It->RecoveryDropBlocks);P->SetNumberField(TEXT("recoveryShotsFired"),It->RecoveryShotsFired);P->SetBoolField(TEXT("recoveryShield"),It->HasRecoveryShield());P->SetBoolField(TEXT("gettingUp"),It->IsGettingUp());P->SetNumberField(TEXT("shieldRemaining"),FMath::Max(0.f,It->RecoveryShield.Until-It->ServerNow()));P->SetBoolField(TEXT("shieldFXVisible"),It->RecoveryFX && It->RecoveryFX->IsVisible());P->SetNumberField(TEXT("shieldArcCount"),It->RecoveryFX?It->RecoveryFX->GetInstanceCount():0);P->SetNumberField(TEXT("shieldGlow"),It->RecoveryFX?It->RecoveryFX->Glow:0);P->SetBoolField(TEXT("knockedOut"),It->IsKnockedOut());P->SetNumberField(TEXT("headZ"),It->GetMesh()->GetSocketLocation(TEXT("head")).Z);P->SetNumberField(TEXT("pelvisZ"),It->GetMesh()->GetSocketLocation(TEXT("pelvis")).Z);P->SetNumberField(TEXT("knockoutRemaining"),FMath::Max(0.f,It->Knockout.Until-It->ServerNow()));P->SetNumberField(TEXT("capsuleHalfHeight"),It->GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
            P->SetBoolField(TEXT("inVent"),It->IsInsideVent());
            const auto& Entry=It->Traversal()->Motion;
            P->SetBoolField(TEXT("ventEntry"),Entry.bEnteringVent);P->SetNumberField(TEXT("ventEntryTime"),Entry.bEnteringVent?Entry.VentPhaseTime+FMath::Clamp(It->ServerNow()-Entry.ServerStart,0.f,Entry.Duration):-1);
            auto BonePoint=[&](const TCHAR* Name){const FVector V=It->GetMesh()->GetSocketLocation(Name);TSharedRef<FJsonObject> Point=MakeShared<FJsonObject>();Point->SetNumberField(TEXT("x"),V.X);Point->SetNumberField(TEXT("y"),V.Y);Point->SetNumberField(TEXT("z"),V.Z);return Point;};
            P->SetObjectField(TEXT("rightPalm"),BonePoint(TEXT("hand_r")));P->SetObjectField(TEXT("leftPalm"),BonePoint(TEXT("hand_l")));P->SetObjectField(TEXT("rightKnee"),BonePoint(TEXT("calf_r")));
            P->SetNumberField(TEXT("bodyPelvisZ"),It->GetMesh()->GetSocketLocation(TEXT("pelvis")).Z);
            P->SetNumberField(TEXT("bodyOriginZ"),It->GetMesh()->GetComponentLocation().Z);
            P->SetNumberField(TEXT("bodyRelativeZ"),It->GetMesh()->GetRelativeLocation().Z);
P->SetBoolField(TEXT("onRope"),It->Traversal()->IsOnRope());P->SetBoolField(TEXT("ropeCrouch"),It->Traversal()->Motion.bVentCrouch);
            P->SetBoolField(TEXT("throwing"),It->IsThrowingGrenade());P->SetNumberField(TEXT("throwTime"),It->ServerNow()-It->ThrowStartedAt);
            P->SetNumberField(TEXT("noiseAge"),It->ServerNow()-It->LastHeardNoise);
            P->SetBoolField(TEXT("restrained"),It->IsRestrained());P->SetBoolField(TEXT("captor"),It->IsCaptor());
            if (It->IsCaptor() && It->IsFinishing() && It->Grab.Partner) P->SetNumberField(TEXT("kickContactDistance"),FVector::Dist(It->GetMesh()->GetSocketLocation(TEXT("foot_l")),It->Grab.Partner->GetMesh()->GetSocketLocation(TEXT("head"))));
            P->SetNumberField(TEXT("finisher"),static_cast<int32>(It->Grab.Finisher));P->SetNumberField(TEXT("finishElapsed"),It->IsFinishing()?It->ServerNow()-It->Grab.FinishStartedAt:0);P->SetNumberField(TEXT("mercGrenades"),It->MercGrenades);P->SetNumberField(TEXT("yaw"),It->GetActorRotation().Yaw);P->SetNumberField(TEXT("maxSpeed"),It->GetCharacterMovement()->MaxWalkSpeed);
            P->SetNumberField(TEXT("grabClipCount"),It->GrabClips.FilterByPredicate([](const auto& Clip){return Clip!=nullptr;}).Num());
            P->SetNumberField(TEXT("grabToken"),It->Grab.Token);P->SetNumberField(TEXT("grabPeerId"),It->Grab.Partner && It->Grab.Partner->GetPlayerState()?It->Grab.Partner->GetPlayerState()->GetPlayerId():-1);
            if (ASPPlayerController* PC=Cast<ASPPlayerController>(It->GetController()))
            {
                TSharedPtr<FJsonObject> Voice;auto VoiceReader=TJsonReaderFactory<>::Create(PC->Voice->Report());
                if (FJsonSerializer::Deserialize(VoiceReader,Voice)) P->SetObjectField(TEXT("voice"),Voice);
            }
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
        int32 ArmedGrenades=0;TArray<TSharedPtr<FJsonValue>> Grenades;
        for (TActorIterator<ASPGrabGrenade> It(W);It;++It)
        {
            if (!It->bExploded) ++ArmedGrenades;
            TSharedRef<FJsonObject> G=MakeShared<FJsonObject>();const FVector L=It->GetActorLocation();
            G->SetStringField(TEXT("name"),It->GetName());G->SetBoolField(TEXT("thrown"),It->bThrown);G->SetBoolField(TEXT("exploded"),It->bExploded);
            G->SetNumberField(TEXT("x"),L.X);G->SetNumberField(TEXT("y"),L.Y);G->SetNumberField(TEXT("z"),L.Z);G->SetNumberField(TEXT("age"),GS->GetServerWorldTimeSeconds()-It->ArmedAt);
            G->SetNumberField(TEXT("bounces"),It->BounceCount);G->SetNumberField(TEXT("ownerId"),It->Captor && It->Captor->GetPlayerState()?It->Captor->GetPlayerState()->GetPlayerId():-1);
            Grenades.Add(MakeShared<FJsonValueObject>(G));
        }
        World->SetArrayField(TEXT("grenades"),Grenades);World->SetNumberField(TEXT("armedGrenades"),ArmedGrenades);
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
        if (Action.StartsWith(TEXT("drop_fps_")))
        {
            static TOptional<float> PreviousCap;
            static uint32 PreviousFlags=0;
            IConsoleVariable* Cap=IConsoleManager::Get().FindConsoleVariable(TEXT("t.MaxFPS"));
            if (!Cap) return TEXT("Frame cap unavailable");
            if (Action==TEXT("drop_fps_restore"))
            {if (PreviousCap.IsSet()) {Cap->Set(PreviousCap.GetValue(),ECVF_SetByConsole);Cap->ClearFlags(ECVF_SetByMask);Cap->SetFlags(static_cast<EConsoleVariableFlags>(PreviousFlags&ECVF_SetByMask));PreviousCap.Reset();}return TEXT("Original frame cap restored");}
            const int32 FPS=FCString::Atoi(*Action.Mid(9));
            if (FPS!=6 && FPS!=10 && FPS!=15 && FPS!=30 && FPS!=60) return TEXT("Use bounded frame cap: 6/10/15/30/60");
            if (!PreviousCap.IsSet()) {PreviousCap=Cap->GetFloat();PreviousFlags=Cap->GetFlags();}
            Cap->Set(FPS,ECVF_SetByConsole);return FString::Printf(TEXT("Temporary editor frame cap %d"),FPS);
        }
        if (Action==TEXT("recovery_camp") || Action==TEXT("recovery_observer"))
        {
            if (Players.Num()!=4) return TEXT("Four players required");
            auto* Merc=Cast<ASPCharacter>(Players[1]->GetPawn());
            if (Action==TEXT("recovery_observer"))
            {
                const FVector Target=Merc->GetActorLocation()+FVector(0,0,10),Location=FVector(-520,-350,150);
                auto* Camera=W->SpawnActor<ACameraActor>(Location,(Target-Location).Rotation());Camera->GetCameraComponent()->SetFieldOfView(60);
                Players[0]->SetViewTarget(Camera);if (Players[0]->GetHUD()) Players[0]->GetHUD()->bShowHUD=false;return TEXT("Recovery review camera active");
            }
            if (!Merc->IsKnockedOut()) return TEXT("Knockout required");
            auto* Spy=Cast<ASPCharacter>(Players[2]->GetPawn());const FVector Air=Merc->GetActorLocation()+FVector(0,0,34+90);
            Spy->GetCharacterMovement()->StopMovementImmediately();Spy->SetActorLocation(Air);Spy->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
            Players[2]->ClientAirPose(Air,FRotator::ZeroRotator,0.f);Spy->ForceNetUpdate();return TEXT("Camp fixture placed above knocked-out merc");
        }
        if (Action==TEXT("drop_attack") || Action==TEXT("drop_miss") || Action==TEXT("drop_covered") || Action==TEXT("drop_fast") || Action==TEXT("drop_host"))
        {
            if (Players.Num()!=4) return TEXT("Four players required");
            const int32 SpyIndex=Action==TEXT("drop_host")?0:2;
            ASPCharacter* Merc=Cast<ASPCharacter>(Players[1]->GetPawn());ASPCharacter* Spy=Cast<ASPCharacter>(Players[SpyIndex]->GetPawn());
            if (Merc->Health<=0 || Spy->Health<=0 || Merc->IsKnockedOut()) return TEXT("Living, recovered players required");
            Merc->SetActorLocationAndRotation(FVector(-250,0,90),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);Merc->ForceNetUpdate();
            if (Action==TEXT("drop_covered"))
            {
                auto* Cover=W->SpawnActor<AStaticMeshActor>(FVector(-250,0,300),FRotator::ZeroRotator);Cover->Tags.Add(TEXT("DropTestCover"));Cover->SetReplicates(true);Cover->SetReplicateMovement(true);Cover->GetStaticMeshComponent()->SetIsReplicated(true);Cover->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);Cover->GetStaticMeshComponent()->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));Cover->SetActorScale3D(FVector(2,2,.2));Cover->GetStaticMeshComponent()->SetCollisionProfileName(TEXT("BlockAll"));
            }
            const float FallSpeed=Action==TEXT("drop_fast")?-1400.f:-250.f;const FVector Air(Action==TEXT("drop_miss")?-110.f:-250.f,0,Action==TEXT("drop_fast")?650.f:570.f);Spy->Traversal()->Drop();Spy->SetActorLocation(Air);Spy->GetCharacterMovement()->SetMovementMode(MOVE_Walking);Spy->GetCharacterMovement()->bWantsToCrouch=false;Spy->GetCharacterMovement()->UnCrouch();Spy->SetActorLocation(Air);Spy->GetCharacterMovement()->SetMovementMode(MOVE_Falling);Spy->GetCharacterMovement()->Velocity=FVector(0,0,FallSpeed);Spy->ForceNetUpdate();
            ASPPlayerController* FallPC=Players[SpyIndex];W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(FallPC,[FallPC,Air,FallSpeed](){FallPC->ClientAirPose(Air,FRotator::ZeroRotator,FallSpeed);}));return TEXT("Authoritative physical drop fixture started");
        }
        if (Action==TEXT("clear_drop_cover"))
        {
            if (Players.Num()==4) if (auto* Spy=Cast<ASPCharacter>(Players[2]->GetPawn()))
            {
                const FVector Ground(-250,-600,90);Spy->GetCharacterMovement()->StopMovementImmediately();Spy->SetActorLocation(Ground,false,nullptr,ETeleportType::TeleportPhysics);Spy->GetCharacterMovement()->SetMovementMode(MOVE_Falling);Spy->ForceNetUpdate();
                // Reset the autonomous owner too, before removing its support.
                // Otherwise its next saved move can make a real unintended drop.
                Players[2]->ClientAirPose(Ground,FRotator::ZeroRotator,0.f);
            }
            for (TActorIterator<AStaticMeshActor> It(W);It;++It) if (It->ActorHasTag(TEXT("DropTestCover"))) It->Destroy();return TEXT("Generated drop-test cover cleared");
        }
        if (Action==TEXT("warehouse_rope"))
        {
            const FRotator R(0,90,0);Pawn->Traversal()->Drop();Pawn->UnCrouch();Pawn->SetActorLocationAndRotation(FVector(-2100,-1545,90),R,false,nullptr,ETeleportType::TeleportPhysics);PC->SetControlRotation(R);Pawn->ForceNetUpdate();
            W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(PC,[PC,R](){PC->ClientSetRotation(R,true);}));return TEXT("Rope approach placed");
        }
        if (Action==TEXT("warehouse_vent_shot"))
        {
            if (Players.Num()!=4) return TEXT("Four players required");
            ASPCharacter* Spy=Cast<ASPCharacter>(Players[2]->GetPawn());ASPCharacter* Merc=Cast<ASPCharacter>(Players[1]->GetPawn());
            if (!Spy->bIsCrouched) return TEXT("Crouch spy first");
            Spy->SetActorLocation(FVector(-2100,-900,824),false,nullptr,ETeleportType::TeleportPhysics);Spy->ForceNetUpdate();
            const FVector M(-2800,-900,514);const FRotator R=(FVector(-2100,-900,824)-(M+FVector(0,0,64))).Rotation();Merc->SetActorLocationAndRotation(M,R,false,nullptr,ETeleportType::TeleportPhysics);Players[1]->SetControlRotation(R);Merc->ForceNetUpdate();
            ASPPlayerController* Shooter=Players[1];W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(Shooter,[Shooter,R](){Shooter->ClientSetRotation(R,true);}));return TEXT("Real vent-wall firing lane placed");
        }
        if (Action==TEXT("warehouse_noise"))
        {
            if (Players.Num()!=4) return TEXT("Four players required");
            for (int32 I:{1,2}) {auto* Body=Cast<ASPCharacter>(Players[I]->GetPawn());Body->Traversal()->Drop();Body->SetActorLocationAndRotation(FVector(I==1?-200.f:200.f,-2000,90),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);Players[I]->SetControlRotation(FRotator::ZeroRotator);Body->ForceNetUpdate();}
            return TEXT("Audible footstep lane placed");
        }
        if (Action==TEXT("vent_review_camera") || Action==TEXT("review_player_view"))
        {
            if (Players.Num()!=1 || !PC->IsLocalController() || !W->GetMapName().Contains(TEXT("Warehouse"))) return TEXT("Solo Warehouse review only");
            if (Action==TEXT("review_player_view")) {PC->SetViewTarget(Pawn);if (PC->GetHUD()) PC->GetHUD()->bShowHUD=true;return TEXT("Player view restored");}
            ACameraActor* Camera=nullptr;for (TActorIterator<ACameraActor> It(W);It;++It) if (It->Tags.Contains(TEXT("VentEntryReview"))) {Camera=*It;break;}
            const FVector Location(-2550,-1630,745),Target(-2100,-1400,785);
            if (!Camera) {Camera=W->SpawnActor<ACameraActor>(Location,(Target-Location).Rotation());Camera->Tags.Add(TEXT("VentEntryReview"));}
            Camera->GetCameraComponent()->SetFieldOfView(60);PC->SetViewTarget(Camera);if (PC->GetHUD()) PC->GetHUD()->bShowHUD=false;return TEXT("Fixed mantle review camera active");
        }
        if (Action==TEXT("review_slow") || Action==TEXT("review_freeze") || Action==TEXT("review_normal"))
        {
            const float Rate=Action==TEXT("review_freeze")?.0001f:Action==TEXT("review_slow")?.1f:1.f;
            for (const FWorldContext& Context:GEngine->GetWorldContexts()) if (UWorld* World=Context.World();World && World->IsGameWorld()) World->GetWorldSettings()->SetTimeDilation(Rate);
            return TEXT("Temporary PIE review speed applied to all test worlds");
        }
        if (Action==TEXT("warehouse_rope_observer") || Action==TEXT("warehouse_throw_observer"))
        {
            if (Players.Num()!=4) return TEXT("Four players required");
            auto* Observer=Players[3];auto* Body=Cast<ASPCharacter>(Observer->GetPawn());
            const bool Rope=Action==TEXT("warehouse_rope_observer");
            const FVector L=Rope?FVector(-2800,-1600,514):FVector(-600,-2000,90);
            const FVector Target=Rope?FVector(-2100,-1420,790):FVector(-200,-2000,145);
            if (!Rope) {auto* Thrower=Cast<ASPCharacter>(Players[1]->GetPawn());Thrower->SetActorLocation(FVector(-200,-2000,90));Thrower->ForceNetUpdate();}
            const FRotator R=(Target-(L+FVector(0,0,64))).Rotation();Body->SetActorLocationAndRotation(L,R,false,nullptr,ETeleportType::TeleportPhysics);Observer->SetControlRotation(R);Body->ForceNetUpdate();
            W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(Observer,[Observer,R](){Observer->ClientSetRotation(R,true);}));return TEXT("Warehouse visual observer placed");
        }
        if (Action==TEXT("grab_observer"))
        {
            if (Players.Num()!=4) return TEXT("Four players required");
            ASPPlayerController* Observer=Players[3];ASPCharacter* Body=Cast<ASPCharacter>(Observer->GetPawn());
            const FVector L(-1100,-1100,90);const FRotator R(0,82.4f,0);Body->SetActorLocationAndRotation(L,R,false,nullptr,ETeleportType::TeleportPhysics);Observer->SetControlRotation(R);Body->ForceNetUpdate();
            W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(Observer,[Observer,R](){Observer->ClientSetRotation(R,true);}));return TEXT("Rescue merc positioned with line of sight to captor");
        }
        if (Action==TEXT("duel_open") || Action==TEXT("duel_blocked") || Action==TEXT("takedown_front") || Action==TEXT("takedown_rear") || Action==TEXT("takedown_range") || Action==TEXT("takedown_wall"))
        {
            if (Players.Num()!=4) return TEXT("Four players required for combat fixture");
            for (int32 Slot:{1,2})
            {
                ASPPlayerController* TargetPC=Players[Slot];ASPCharacter* Target=Cast<ASPCharacter>(TargetPC->GetPawn());
                if (!Target || Target->Health<=0) return TEXT("Combat fixture requires living players");
                const bool Merc=Slot==1;const bool Takedown=Action.StartsWith(TEXT("takedown"));
                FVector L(Merc?(Takedown?-1000.f:(Action==TEXT("duel_open")?-700.f:-450.f)):-1100.f,Action==TEXT("duel_blocked")?-400.f:-800.f,90.f);
                if (!Merc && Action==TEXT("takedown_range")) L.X=-1200.f;
                if (Action==TEXT("takedown_wall")) L.X=Merc?-100.f:-200.f;
                const FRotator R(0,Merc && Action!=TEXT("takedown_rear") && Action!=TEXT("takedown_range") && Action!=TEXT("takedown_wall")?180.f:0.f,0);
                Target->Traversal()->Drop();Target->UnCrouch();Target->SetActorLocation(L,false,nullptr,ETeleportType::TeleportPhysics);
                Target->SetActorRotation(R);TargetPC->SetControlRotation(R);Target->ForceNetUpdate();
                W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(TargetPC,[TargetPC,R]() {TargetPC->ClientSetRotation(R,true);}));
            }
            return TEXT("Combat fixture placed");
        }
        if (Action==TEXT("place_ledge") || Action==TEXT("place_vault") || Action==TEXT("place_terminal") || Action==TEXT("place_open") || Action==TEXT("place_camera_wall"))
        {
            Pawn->Traversal()->Drop();Pawn->UnCrouch();
            FVector L;FRotator R;
            if (Action==TEXT("place_ledge")) {L=FVector(-1050,560,90);R=FRotator(0,90,0);}
            else if (Action==TEXT("place_vault")) {L=FVector(-480,0,90);R=FRotator::ZeroRotator;}
            else if (Action==TEXT("place_terminal")) {L=FVector(-100,0,90);R=FRotator::ZeroRotator;}
            else if (Action==TEXT("place_camera_wall")) {L=FVector(-1000,-400,90);R=FRotator::ZeroRotator;}
            else {L=FVector(-1100,-800,90);R=FRotator::ZeroRotator;}
            Pawn->SetActorLocation(L,false,nullptr,ETeleportType::TeleportPhysics);Pawn->SetActorRotation(R);PC->SetControlRotation(R);
            W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(PC,[PC,R]() {PC->ClientSetRotation(R,true);}));
            Pawn->ForceNetUpdate();return TEXT("Placed for editor test");
        }
        if (Action==TEXT("grenade_stop_open") || Action==TEXT("grenade_stop_cover"))
        {
            if (Players.Num()!=4) return TEXT("Four players required");
            for (TActorIterator<ASPGrabGrenade> It(W);It;++It) if (It->bThrown && !It->bExploded && It->Captor==Pawn)
            {
                It->Projectile->StopMovementImmediately();It->Projectile->Deactivate();
                const bool Cover=Action==TEXT("grenade_stop_cover");It->SetActorLocation(Cover?FVector(-70,-800,30):FVector(-200,-800,25));It->ForceNetUpdate();
                ASPCharacter* Target=Cast<ASPCharacter>(Players[2]->GetPawn());Target->SetActorLocation(Cover?FVector(90,-800,90):FVector(-200,-800,90),false,nullptr,ETeleportType::TeleportPhysics);Target->ForceNetUpdate();
                return TEXT("Existing thrown grenade settled at fixed blast/cover fixture; original fuse preserved");
            }
            return TEXT("Throw a merc grenade before settling the blast fixture");
        }
        if (Action==TEXT("grenade_blocked_release"))
        {
            const FRotator Facing=FRotator::ZeroRotator;Pawn->SetActorLocationAndRotation(FVector(-85,-800,90),Facing,false,nullptr,ETeleportType::TeleportPhysics);PC->SetControlRotation(Facing);Pawn->ForceNetUpdate();
            W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(PC,[PC,Facing](){PC->ClientSetRotation(Facing,true);}));return TEXT("Merc placed directly beside partition for release clearance check");
        }
        if (Action==TEXT("grenades_empty") || Action==TEXT("grenades_full")) {Pawn->MercGrenades=Action==TEXT("grenades_empty")?0:2;Pawn->ForceNetUpdate();return TEXT("Merc grenade inventory fixture set");}
        if (Action==TEXT("expire_camera"))
        {if (Pawn->DeployedCamera) Pawn->DeployedCamera->SetLifeSpan(.2f);return TEXT("Camera lifespan shortened for test");}
        if (Action==TEXT("camera_front") || Action==TEXT("camera_behind"))
        {
            if (Players.Num()!=4) return TEXT("Four players required");
            const ASPCharacter* Shooter=Cast<ASPCharacter>(Players[2]->GetPawn());
            const ASPStickyCamera* Camera=Shooter?Shooter->DeployedCamera.Get():nullptr;
            if (!Camera) return TEXT("Remote spy needs a camera");
            ASPCharacter* Merc=Cast<ASPCharacter>(Players[1]->GetPawn());
            FVector Position=Camera->GetActorLocation()+Camera->GetActorForwardVector()*(Action==TEXT("camera_front")?250.f:-250.f);Position.Z=90;
            Merc->SetActorLocation(Position,false,nullptr,ETeleportType::TeleportPhysics);Merc->ForceNetUpdate();
            ASPCharacter* Friend=Cast<ASPCharacter>(Players[0]->GetPawn());
            Position=Camera->GetActorLocation()+Camera->GetActorForwardVector()*220.f+FVector(0,130,0);Position.Z=90;
            Friend->SetActorLocation(Position,false,nullptr,ETeleportType::TeleportPhysics);Friend->ForceNetUpdate();
            return TEXT("Camera gas range and cover fixture placed");
        }
        if (Action==TEXT("expire_sensors"))
        {for (TActorIterator<ASPSpyBulletSensor> It(W);It;++It) It->Destroy();return TEXT("Spy sensors expired for test");}
        if (Action==TEXT("sensor_exit") || Action==TEXT("sensor_return"))
        {
            if (Players.Num()!=4) return TEXT("Four players required");
            ASPCharacter* Target=Cast<ASPCharacter>(Players[1]->GetPawn());
            Target->SetActorLocation(Action==TEXT("sensor_exit")?FVector(1250,-800,90):FVector(-450,-400,90),false,nullptr,ETeleportType::TeleportPhysics);
            Target->ForceNetUpdate();return TEXT("Sensor range fixture placed");
        }
        if (Action==TEXT("expire")) {W->GetGameState<ASPGameState>()->RoundSeconds=.1f;return TEXT("Round timer shortened for test");}
        if (Action==TEXT("near_complete")) {W->GetGameState<ASPGameState>()->HackProgress=.99f;return TEXT("Hack progress set for win-condition test");}
        if (Action==TEXT("damage") || Action==TEXT("wound"))
        {
            const float Amount=Action==TEXT("wound")?10.f:100.f;
            W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(Pawn,[Pawn,Amount]() {FDamageEvent Event;Pawn->TakeDamage(Amount,Event,nullptr,nullptr);}));
            return TEXT("Damage queued on game tick");
        }
        if (Action==TEXT("disconnect"))
        {
            W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(PC,[PC]() {if (UNetConnection* Connection=PC->GetNetConnection()) Connection->Close();}));
            return TEXT("Remote connection close queued");
        }
        if (Action==TEXT("recreate_pawn"))
        {
            W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(PC,[PC,W]() {W->GetAuthGameMode<ASPGameMode>()->Respawn(PC);}));return TEXT("Pawn recreation queued");
        }
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
        const TArray<FString> Allowed={TEXT("traverse"),TEXT("drop"),TEXT("hack"),TEXT("release"),TEXT("fire"),TEXT("role"),TEXT("spy"),TEXT("merc"),TEXT("crouch"),TEXT("nightvision"),TEXT("camera_noise_rpc"),TEXT("camera_gas_rpc"),TEXT("foreign_camera_rpc"),TEXT("voice_probe"),TEXT("voice_auto"),TEXT("voice_team"),TEXT("voice_old_epoch"),TEXT("voice_grab"),TEXT("voice_stale"),TEXT("voice_reset_stats")};
        if (!Allowed.Contains(Action) && !Action.StartsWith(TEXT("pad_"))) return TEXT("Unknown test action");
        // Native MCP executes in editor context. Dispatch RPCs during the game world's
        // tick so PIE chooses the owning client's network callspace correctly.
        W->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(PC,[PC,Action]() { PC->ClientExercise(Action); }));
        return TEXT("Owning-client input queued for game tick");
    }
#endif
    return TEXT("Editor game world not available");
}

void ASPPlayerController::ClientAirPose_Implementation(FVector Position,FRotator Facing,float FallingSpeed)
{
#if WITH_EDITOR
    if (auto* P=Cast<ASPCharacter>(GetPawn()))
    {P->SetActorLocation(Position);P->GetCharacterMovement()->SetMovementMode(MOVE_Walking);P->GetCharacterMovement()->bWantsToCrouch=false;P->GetCharacterMovement()->UnCrouch();P->SetActorLocationAndRotation(Position,Facing,false,nullptr,ETeleportType::TeleportPhysics);SetControlRotation(Facing);P->GetCharacterMovement()->SetMovementMode(MOVE_Falling);P->GetCharacterMovement()->Velocity=FVector(0,0,FallingSpeed);}
#endif
}
