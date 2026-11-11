#include "Prototype.h"
#include "SPWarehouse.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/Canvas.h"
#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "GameFramework/PlayerStart.h"
#include "Net/UnrealNetwork.h"
#include "Kismet/GameplayStatics.h"
#include "InputKeyEventArgs.h"

bool ASPPlayerController::InputKey(const FInputKeyEventArgs& Params)
{
#if WITH_EDITOR
    if (bAutomatedInput && !Params.IsSimulatedInput()) return true;
#endif
    if (Params.Event==IE_Pressed && Params.Key==EKeys::One) {bUsingGamepad=false;PracticeSpy();return true;}
    if (Params.Event==IE_Pressed && Params.Key==EKeys::Two) {bUsingGamepad=false;PracticeMerc();return true;}
    if (Params.Event!=IE_Released && FMath::Abs(Params.AmountDepressed)>.2f)
        bUsingGamepad=Params.Key.IsGamepadKey();
    return Super::InputKey(Params);
}

void ASPPlayerState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(ASPPlayerState, Team);
}
void ASPGameState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(ASPGameState, VoiceEpoch);
    DOREPLIFETIME(ASPGameState, Phase);
    DOREPLIFETIME(ASPGameState, bPractice);
    DOREPLIFETIME(ASPGameState, RoundSeconds);
    DOREPLIFETIME(ASPGameState, HackProgress);
    DOREPLIFETIME(ASPGameState, Spies);
    DOREPLIFETIME(ASPGameState, Mercs);
}

ASPGameMode::ASPGameMode()
{
    PrimaryActorTick.bCanEverTick = true;
    DefaultPawnClass = ASPCharacter::StaticClass();
    PlayerStateClass = ASPPlayerState::StaticClass();
    GameStateClass = ASPGameState::StaticClass();
    HUDClass = ASPHUD::StaticClass();
    PlayerControllerClass = ASPPlayerController::StaticClass();
}
void ASPGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
    Super::InitGame(MapName, Options, ErrorMessage);
#if !UE_BUILD_SHIPPING
    bPracticeRequested = GetNetMode()==NM_Standalone && !UGameplayStatics::HasOption(Options,TEXT("Competitive"));
#endif
    if (UClass* PlayerBP=LoadClass<ASPCharacter>(nullptr,TEXT("/Game/Prototype/BP_Player.BP_Player_C"))) DefaultPawnClass=PlayerBP;
    const bool Warehouse=MapName.Contains(TEXT("Warehouse"));
    if (Warehouse) {if (!TActorIterator<ASPWarehouse>(GetWorld())) GetWorld()->SpawnActor<ASPWarehouse>();}
    else GetWorld()->SpawnActor<ASPArena>();
    Terminal = GetWorld()->SpawnActor<ASPTerminal>(FVector(0,0,60), FRotator::ZeroRotator);
    for (int32 Index=0; Index<4; ++Index)
    {
        const bool bSpy = Index < 2;
        FVector Spawn(bSpy?-1250.f:1250.f,Index%2?550.f:-550.f,100.f);FRotator Facing(0,bSpy?0.f:180.f,0);
        if (Warehouse) {Spawn=bSpy?FVector(Index%2?2100.f:-2100.f,Index%2?1560.f:-1560.f,100.f):FVector(Index%2?65.f:-65.f,Index%2?-2500.f:-2600.f,100.f);Facing=FRotator(0,bSpy && Index%2?-90.f:90.f,0);}
        APlayerStart* Start = GetWorld()->SpawnActor<APlayerStart>(
            Spawn,Facing);
        if (Start) Start->PlayerStartTag = bSpy ? TEXT("Spy") : TEXT("Merc");
    }
}
void ASPGameMode::InitGameState()
{
    Super::InitGameState();
    GetGameState<ASPGameState>()->bPractice=bPracticeRequested;
}
void ASPPlayerController::Practice()
{
#if !UE_BUILD_SHIPPING
    if (GetNetMode()==NM_Standalone) UGameplayStatics::OpenLevel(this,TEXT("/Game/Maps/Warehouse"),true,TEXT("Practice=1"));
#endif
}
void ASPPlayerController::Match()
{
#if !UE_BUILD_SHIPPING
    if (GetNetMode()==NM_Standalone) UGameplayStatics::OpenLevel(this,TEXT("/Game/Maps/Warehouse"),true,TEXT("Competitive=1"));
#endif
}
void ASPPlayerController::PracticeSpy() {if (ASPCharacter* P=Cast<ASPCharacter>(GetPawn())) P->ChoosePracticeRole(ESPTeam::Spy);}
void ASPPlayerController::PracticeMerc() {if (ASPCharacter* P=Cast<ASPCharacter>(GetPawn())) P->ChoosePracticeRole(ESPTeam::Merc);}
void ASPGameMode::PreLogin(const FString& Options, const FString& Address,
    const FUniqueNetIdRepl& UniqueId, FString& ErrorMessage)
{
    Super::PreLogin(Options, Address, UniqueId, ErrorMessage);
    if (GetNumPlayers() >= 4) ErrorMessage = TEXT("This prototype has four player slots (2v2).");
}
void ASPGameMode::RefreshRoster(AController* Exclude)
{
    ASPGameState* GS = GetGameState<ASPGameState>();
    GS->Spies = GS->Mercs = 0;
    for (FConstPlayerControllerIterator It=GetWorld()->GetPlayerControllerIterator(); It; ++It)
    {
        APlayerController* PC = It->Get();
        if (!PC || PC == Exclude) continue;
        if (ASPPlayerState* PS = PC->GetPlayerState<ASPPlayerState>())
            (PS->Team == ESPTeam::Spy ? GS->Spies : GS->Mercs)++;
    }
}
void ASPGameMode::PostLogin(APlayerController* NewPlayer)
{
    RefreshRoster(NewPlayer);
    ASPGameState* GS = GetGameState<ASPGameState>();
    if (GS->Spies + GS->Mercs >= 4)
    {
        NewPlayer->ClientReturnToMainMenuWithTextReason(FText::FromString(TEXT("Match full.")));
        return;
    }
    if (ASPPlayerState* PS = NewPlayer->GetPlayerState<ASPPlayerState>())
        PS->Team = GS->Spies <= GS->Mercs ? ESPTeam::Spy : ESPTeam::Merc;
    NewPlayer->StartSpot = nullptr;
    Super::PostLogin(NewPlayer);
    RefreshRoster();
}
void ASPGameMode::Logout(AController* Exiting)
{
    if (Exiting) if (ASPCharacter* P=Cast<ASPCharacter>(Exiting->GetPawn())) P->EndGrab();
    Super::Logout(Exiting);
    if (GetWorld()->bIsTearingDown || GetWorld()->IsBeingCleanedUp()) return;
    RefreshRoster(Exiting);
    ResetRound(Exiting);
}
AActor* ASPGameMode::ChoosePlayerStart_Implementation(AController* Player)
{
    const ASPPlayerState* PS = Player ? Player->GetPlayerState<ASPPlayerState>() : nullptr;
    const FName Tag = PS && PS->Team == ESPTeam::Merc ? TEXT("Merc") : TEXT("Spy");
    AActor* Best = nullptr;
    double BestClearance = -1;
    for (TActorIterator<APlayerStart> It(GetWorld()); It; ++It)
    {
        if (It->PlayerStartTag != Tag) continue;
        double Clearance = TNumericLimits<double>::Max();
        for (TActorIterator<ASPCharacter> Pawn(GetWorld()); Pawn; ++Pawn)
            if (Pawn->Health > 0.f)
                Clearance = FMath::Min(Clearance, FVector::DistSquared(It->GetActorLocation(), Pawn->GetActorLocation()));
        if (Clearance > BestClearance) { Best = *It; BestClearance = Clearance; }
    }
    return Best ? Best : Super::ChoosePlayerStart_Implementation(Player);
}
void ASPGameMode::Respawn(AController* Player)
{
    if (!IsValid(Player)) return;
    if (APawn* Old = Player->GetPawn()) { Player->UnPossess(); Old->Destroy(); }
    RestartPlayer(Player);
}
void ASPGameMode::ResetRound(AController* Exclude)
{
    ASPGameState* GS = GetGameState<ASPGameState>();
    ++GS->VoiceEpoch;GS->ForceNetUpdate();
    GS->Phase = ESPPhase::Waiting;
    GS->RoundSeconds = 180.f;
    GS->HackProgress = 0.f;
    ResultSeconds = 0.f;
    for (FConstPlayerControllerIterator It=GetWorld()->GetPlayerControllerIterator(); It; ++It)
        if (APlayerController* PC = It->Get())
            if (PC != Exclude)
            {
                if (ASPPlayerController* VoicePC=Cast<ASPPlayerController>(PC)) VoicePC->ClientVoiceEpoch(GS->VoiceEpoch);
                Respawn(PC);
            }
}
void ASPGameMode::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    ASPGameState* GS = GetGameState<ASPGameState>();
    if (!GS || !Terminal || GS->bPractice) return;
    if (GS->Phase == ESPPhase::Waiting)
    {
        if (GS->Spies == 2 && GS->Mercs == 2) GS->Phase = ESPPhase::Playing;
        return;
    }
    if (GS->Phase != ESPPhase::Playing)
    {
        ResultSeconds += DeltaSeconds;
        if (ResultSeconds >= 8.f) ResetRound();
        return;
    }
    bool bHacking = false;
    for (TActorIterator<ASPCharacter> It(GetWorld()); It; ++It)
    {
        if (!It->IsSpy() || !It->WantsToHack()
            || FVector::Dist(It->GetActorLocation(), Terminal->GetActorLocation()) > It->HackReach) continue;
        FHitResult Hit;
        FCollisionQueryParams Query(SCENE_QUERY_STAT(HackSight), false, *It);
        const bool bBlocked = GetWorld()->LineTraceSingleByChannel(Hit,
            It->GetActorLocation(), Terminal->GetActorLocation(), ECC_Visibility, Query);
        if (!bBlocked || Hit.GetActor() == Terminal) bHacking = true;
    }
    // Two spies cannot stack speed. Released progress persists for this prototype.
    if (bHacking) GS->HackProgress = FMath::Min(1.f, GS->HackProgress + DeltaSeconds / 20.f);
    GS->RoundSeconds = FMath::Max(0.f, GS->RoundSeconds - DeltaSeconds);
    if (GS->HackProgress >= 1.f) GS->Phase = ESPPhase::SpiesWin;
    else if (GS->RoundSeconds <= 0.f) GS->Phase = ESPPhase::MercsWin;
}

void ASPHUD::DrawHUD()
{
    Super::DrawHUD();if (!Canvas || !PlayerOwner) return;
    const ASPGameState* GS=GetWorld()->GetGameState<ASPGameState>();const ASPCharacter* P=Cast<ASPCharacter>(PlayerOwner->GetPawn());if (!GS || !P) return;
    LastDrawTime=GetWorld()->GetTimeSeconds();const float W=Canvas->ClipX,H=Canvas->ClipY,S=H/720.f,M=W*.045f;
    const FLinearColor Ink(.015,.02,.025,.85),White(.95,.95,.89,1),Gold(.92,.69,.31,1),Blue(.48,.82,.81,1);const FLinearColor Accent=P->IsSpy()?Blue:Gold;
    auto Label=[&](const FString& T,float X,float Y,FLinearColor C=FLinearColor::White,float Size=.82f){DrawText(T,C,X,Y,GEngine->GetMediumFont(),S*Size*1.25f);};
    auto Panel=[&](float X,float Y,float Width,float Height){DrawRect(FLinearColor(.015,.02,.025,.65),X,Y,Width,Height);DrawRect(Accent,X,Y,2*S,Height);};
    Label(P->IsSpy()?TEXT("INFILTRATION"):TEXT("SECURITY"),M,32*S,Accent,1.f);
    Label(GetWorld()->GetMapName().Contains(TEXT("Warehouse"))?TEXT("WAREHOUSE / 01"):TEXT("TRAINING"),M,57*S,White,.65f);
    const FString Clock=GS->bPractice?TEXT("PRACTICE"):FString::Printf(TEXT("%02d:%02d"),FMath::CeilToInt(GS->RoundSeconds)/60,FMath::CeilToInt(GS->RoundSeconds)%60);
    Label(Clock,W*.48f,28*S,White,1.12f);Label(FString::Printf(TEXT("VAULT  %02d%%"),FMath::RoundToInt(GS->HackProgress*100)),W*.46f,57*S,White,.66f);
    if (!GS->bPractice && GS->Phase!=ESPPhase::Playing)
        Label(GS->Phase==ESPPhase::Waiting?TEXT("WAITING FOR BOTH TEAMS"):GS->Phase==ESPPhase::SpiesWin?TEXT("SPIES WIN"):TEXT("MERCS WIN"),W*.37f,91*S,Accent,.95f);
    Panel(M,H-113*S,232*S,70*S);Label(TEXT("HEALTH"),M+14*S,H-104*S,White,.62f);Label(FString::FromInt(FMath::CeilToInt(P->Health)),M+163*S,H-105*S,White,1.f);
    for (int32 I=0;I<10;++I) DrawRect(P->Health>I*10?Accent:FLinearColor(.15,.17,.18,1),M+(14+I*20)*S,H-74*S,16*S,5*S);
    const ASPPlayerController* PC=Cast<ASPPlayerController>(PlayerOwner);
    if (PC && PC->Voice) Label(PC->Voice->bMicMuted?TEXT("MIC MUTED"):P->IsRestrained()?TEXT("GRAB VOICE / OPEN"):TEXT("TEAM VOICE / OPEN"),M+14*S,H-59*S,White,.57f);
    const float Right=W-M-255*S;Panel(Right,H-128*S,255*S,85*S);
    if (!P->IsSpy())
    {Label(P->WeaponMode()==ESPWeapon::Hands?TEXT("CARBINE / SLUNG"):TEXT("CARBINE"),Right+16*S,H-117*S,White,.88f);
     Label(FString::Printf(TEXT("RB   FRAG  %d"),P->MercGrenades),Right+16*S,H-88*S,P->MercGrenades>0?Gold:FLinearColor(.55,.55,.52,1),.85f);
     Label(P->FlashlightEnabled()?TEXT("UP  LIGHT ON"):TEXT("UP  FLASHLIGHT"),Right+16*S,H-63*S,White,.58f);}
    else {Label(TEXT("Y   HANDS / SHOCKER"),Right+16*S,H-117*S,White,.75f);Label(FString::Printf(TEXT("RB  %s  %d%s"),P->SelectedGadget()==ESPSpyGadget::StickyCamera?TEXT("CAMERA"):TEXT("SPY BULLET"),P->GadgetAmmo(),P->GadgetAmmo()==0?TEXT(" EMPTY"):TEXT("")),Right+16*S,H-88*S,Accent,.72f);Label(FString::Printf(TEXT("CAM %d / DART %d   |   DOWN SELECT"),P->GadgetInventory.Cameras,P->GadgetInventory.TrackingDarts),Right+16*S,H-63*S,White,.58f);}
    if (GS->bPractice) Label(TEXT("D-PAD RIGHT  SWITCH ROLE    /    LEFT  INSPECT"),M,86*S,White,.59f);
    FString Context;
    if (P->IsChokeVictim()) Context=FString::Printf(TEXT("BACK CHOKE %.1f | LS MOVE / RS AIM / RT FIRE / RB GRENADE"),FMath::Max(0.f,5.f-(P->ServerNow()-P->Grab.FinishStartedAt)));
    else if (P->IsRestrained()) Context=P->IsCaptor()?TEXT("LS MOVE / RS TURN   |   TAP RT SNAP / HOLD RT FINISH   |   B RELEASE"):TEXT("GRABBED / VOICE LINK OPEN");
    else if (P->Traversal()->IsOnRope()) Context=TEXT("LS UP / DOWN    |    B DROP");
    else if (P->IsInsideVent()) Context=TEXT("VENT ROUTE   /   UP NIGHT VISION   /   A GRAB ROPE AT MOUTH");
    else if (P->IsThrowingGrenade()) Context=TEXT("FRAG OUT");
    else if (const ASPStickyCamera* V=Cast<ASPStickyCamera>(PlayerOwner->GetViewTarget())) Context=FString::Printf(TEXT("CAMERA %.1fx  |  LT/RT ZOOM  |  X NOISE  |  B GAS %s  |  LB EXIT"),85.f/V->Camera->FieldOfView,V->GasAvailable()?TEXT("READY"):TEXT("EMPTY"));
    if (!Context.IsEmpty()) {float TW,TH;GetTextSize(Context,TW,TH,GEngine->GetMediumFont(),S*.7f*1.25f);Label(Context,FMath::Max(M,(W-TW)*.5f),H-158*S,White,.7f);}
    if (P->FeedbackUntil>GetWorld()->GetTimeSeconds()) Label(P->Feedback,W*.29f,H-195*S,Accent,.68f);
    if (P->Health<=0) Label(TEXT("DOWN / RESPAWN IN 5 SECONDS"),W*.34f,H*.43f,White,1.f);
    if (P->IsKnockedOut()) Label(FString::Printf(TEXT("KNOCKED OUT / %d"),FMath::Max(0,FMath::CeilToInt(P->Knockout.Until-P->ServerNow()))),W*.4f,H*.42f,Gold,1.f);
    else if (P->IsGettingUp()) Label(TEXT("GETTING UP / RECOVERY SHIELD"),W*.33f,H*.42f,Blue,.8f);
    else if (P->IsStunned()) Label(TEXT("STUNNED"),W*.45f,H*.42f,Gold,1.f);
    if (P->HasRecoveryShield()) Label(FString::Printf(TEXT("RECOVERY SHIELD %.1fs"),FMath::Max(0.f,P->RecoveryShield.Until-P->ServerNow())),M,H-135*S,Blue,.68f);
    if (P->NightVisionEnabled()) Label(TEXT("NIGHT VISION"),M,113*S,Blue,.65f);
    if (P->HasReticle() && !P->IsThrowingGrenade())
    {
        const FVector2D C(W*.5f,H*.5f);const float R=FMath::Clamp(P->ReticleGap(),7.f,28.f)*S;
        auto Line=[&](FVector2D A,FVector2D B,FLinearColor Color,float Thick){DrawLine(A.X,A.Y,B.X,B.Y,Ink,Thick+2*S);DrawLine(A.X,A.Y,B.X,B.Y,Color,Thick);};
        if (!P->IsSpy())
        {
            const FLinearColor Amber(1.f,.67f,.16f,.88f);
            const float Radius=(P->IsAiming()?28.f:36.f)*S+FMath::Min(5.f,P->GetVelocity().Size2D()*.012f)*S;
            for (int32 Pass=0;Pass<2;++Pass) for (int32 Ring=0;Ring<2;++Ring) for (int32 Side=0;Side<2;++Side) for (int32 I=0;I<28;++I)
            {
                const float A=FMath::DegreesToRadians(Side*180.f+8.f+I*5.86f),B=A+FMath::DegreesToRadians(5.86f),Rad=Radius-Ring*5.f*S;
                const FVector2D Start=C+FVector2D(FMath::Cos(A),FMath::Sin(A))*Rad,End=C+FVector2D(FMath::Cos(B),FMath::Sin(B))*Rad;
                DrawLine(Start.X,Start.Y,End.X,End.Y,Pass?Amber:Ink,((Ring?1.1f:1.8f)+(Pass?0.f:2.f))*S);
            }
            DrawRect(Ink,C.X-2.5f*S,C.Y-2.5f*S,5*S,5*S);DrawRect(Amber,C.X-1.5f*S,C.Y-1.5f*S,3*S,3*S);
        }
        else
        {
            for (int32 Q=0;Q<4;++Q) for (int32 I=0;I<9;++I)
            {
                const float A=FMath::DegreesToRadians(Q*90.f+20+I*5.5f),B=A+FMath::DegreesToRadians(5.5f);
                Line(C+FVector2D(FMath::Cos(A),FMath::Sin(A))*R,C+FVector2D(FMath::Cos(B),FMath::Sin(B))*R,White,1.1f*S);
            }
            DrawRect(Ink,C.X-2*S,C.Y-2*S,4*S,4*S);DrawRect(White,C.X-S,C.Y-S,2*S,2*S);
        }
        if (!P->IsSpy() && P->ServerNow()-P->LastHeardNoise<.75f)
        {
            const FVector D=FRotator(0,-P->GetBaseAimRotation().Yaw,0).RotateVector(P->HeardNoisePosition-P->GetActorLocation());
            const float A=FMath::RoundToFloat(FMath::Atan2(D.Y,D.X)/(PI/4))*(PI/4);const FVector2D N(FMath::Sin(A),-FMath::Cos(A));
            const FVector2D At=C+N*(R+35*S);
            const float Bearing=FMath::Atan2(N.Y,N.X),Fade=FMath::Clamp(1.f-(P->ServerNow()-P->LastHeardNoise)/.75f,0.f,1.f);
            FLinearColor Cue=Gold;Cue.A=Fade*.9f;
            for (int32 Ring=0;Ring<3;++Ring) for (int32 I=0;I<16;++I)
            {
                const float ArcStart=Bearing+FMath::DegreesToRadians(-35.f+I*4.375f),ArcEnd=ArcStart+FMath::DegreesToRadians(4.375f),Radius=R+(12.f+Ring*7.f)*S;
                DrawLine(C.X+FMath::Cos(ArcStart)*Radius,C.Y+FMath::Sin(ArcStart)*Radius,C.X+FMath::Cos(ArcEnd)*Radius,C.Y+FMath::Sin(ArcEnd)*Radius,Cue,1.8f*S);
            }
            if (FMath::Abs(D.Z)>120) Label(D.Z>0?TEXT("^"):TEXT("v"),At.X-3*S,At.Y-16*S,Gold,.65f);
        }
        if ((P->Feedback==TEXT("Hit") || P->Feedback==TEXT("Target down")) && P->FeedbackUntil-GetWorld()->GetTimeSeconds()>1.8f)
            for (int32 X:{-1,1}) for (int32 Y:{-1,1}) Line(C+FVector2D(X*8*S,Y*8*S),C+FVector2D(X*13*S,Y*13*S),White,1.4f*S);
    }
    // Spy radar contains only contacts admitted by the existing gameplay rules.
    if (P->IsSpy())
    {
        const FVector2D C(W-M-53*S,122*S);const float R=42*S;
        for (int32 I=0;I<40;++I) {const float A=I*2*PI/40,B=(I+1)*2*PI/40;DrawLine(C.X+FMath::Cos(A)*R,C.Y+FMath::Sin(A)*R,C.X+FMath::Cos(B)*R,C.Y+FMath::Sin(B)*R,FLinearColor(.3,.5,.5,.5),S);}
        DrawRect(Blue,C.X-1.5*S,C.Y-1.5*S,3*S,3*S);
        for (const ASPCharacter* T:P->RadarTargets()) {const FVector D=FRotator(0,-P->GetBaseAimRotation().Yaw,0).RotateVector(T->GetActorLocation()-P->GetActorLocation());const FVector2D O=FVector2D(D.Y,-D.X).GetClampedToMaxSize(3000)*(R/3000);DrawRect(Gold,C.X+O.X-2*S,C.Y+O.Y-2*S,4*S,4*S);}
    }
}

void ASPPlayerController::ClientExercise_Implementation(const FString& Action)
{
#if WITH_EDITOR
    if (Action==TEXT("spy")) {PracticeSpy();return;}
    if (Action==TEXT("merc")) {PracticeMerc();return;}
    if (Action==TEXT("automation_on") || Action==TEXT("automation_off"))
    {bAutomatedInput=Action==TEXT("automation_on");if (PlayerInput) PlayerInput->FlushPressedKeys();return;}
    const TMap<FString,FKey> PadKeys={{TEXT("a"),EKeys::Gamepad_FaceButton_Bottom},{TEXT("b"),EKeys::Gamepad_FaceButton_Right},
        {TEXT("x"),EKeys::Gamepad_FaceButton_Left},{TEXT("y"),EKeys::Gamepad_FaceButton_Top},
        {TEXT("rt"),EKeys::Gamepad_RightTrigger},{TEXT("lt"),EKeys::Gamepad_LeftTrigger},
        {TEXT("role"),EKeys::Gamepad_DPad_Right},{TEXT("equipment"),EKeys::Gamepad_DPad_Up},{TEXT("inspect"),EKeys::Gamepad_DPad_Left},{TEXT("camera"),EKeys::Gamepad_LeftShoulder},{TEXT("gadget"),EKeys::Gamepad_RightShoulder},{TEXT("select_gadget"),EKeys::Gamepad_DPad_Down},{TEXT("move"),EKeys::Gamepad_LeftY},{TEXT("sneak"),EKeys::Gamepad_LeftY},{TEXT("back"),EKeys::Gamepad_LeftY},{TEXT("drift"),EKeys::Gamepad_LeftY},{TEXT("look"),EKeys::Gamepad_RightX},{TEXT("look_pitch"),EKeys::Gamepad_RightY},{TEXT("mic_mute"),EKeys::Gamepad_Special_Left}};
    if (Action.StartsWith(TEXT("pad_")))
    {
        FString Button=Action.Mid(4);const bool Released=Button.RemoveFromEnd(TEXT("_up"));
        Button.RemoveFromEnd(TEXT("_down"));
        if (const FKey* Key=PadKeys.Find(Button))
            InputKey(FInputKeyEventArgs::CreateSimulated(*Key,Key->IsAnalog()?IE_Axis:(Released?IE_Released:IE_Pressed),Released?0.f:(Button==TEXT("back")?-1.f:Button==TEXT("sneak")?.3f:Button==TEXT("drift")?.1f:1.f)));
        return;
    }
    if (Action==TEXT("voice_probe")) {Voice->ProbeMicrophone();return;}
    if (Action==TEXT("voice_auto")) {Voice->Synthetic(Voice->DesiredChannel());return;}
    if (Action==TEXT("voice_team")) {Voice->Synthetic(ESPVoiceChannel::Team);return;}
    if (Action==TEXT("voice_grab")) {Voice->Synthetic(ESPVoiceChannel::Grab);return;}
    if (Action==TEXT("voice_old_epoch")) {Voice->Synthetic(ESPVoiceChannel::Team,true);return;}
    if (Action==TEXT("voice_stale")) {Voice->Synthetic(ESPVoiceChannel::Grab,true);return;}
    if (Action==TEXT("voice_reset_stats")) {Voice->ResetStats();return;}
    if (ASPCharacter* Pawn=Cast<ASPCharacter>(GetPawn())) Pawn->Exercise(Action);
#endif
}
