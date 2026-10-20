#include "Prototype.h"
#include "Engine/Canvas.h"
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
    GetWorld()->SpawnActor<ASPArena>();
    Terminal = GetWorld()->SpawnActor<ASPTerminal>(FVector(0,0,60), FRotator::ZeroRotator);
    for (int32 Index=0; Index<4; ++Index)
    {
        const bool bSpy = Index < 2;
        APlayerStart* Start = GetWorld()->SpawnActor<APlayerStart>(
            FVector(bSpy ? -1250.f : 1250.f, Index % 2 ? 550.f : -550.f, 100.f),
            FRotator(0,bSpy ? 0.f : 180.f,0));
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
    if (GetNetMode()==NM_Standalone) UGameplayStatics::OpenLevel(this,TEXT("/Game/Maps/Prototype"),true,TEXT("Practice=1"));
#endif
}
void ASPPlayerController::Match()
{
#if !UE_BUILD_SHIPPING
    if (GetNetMode()==NM_Standalone) UGameplayStatics::OpenLevel(this,TEXT("/Game/Maps/Prototype"),true,TEXT("Competitive=1"));
#endif
}
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
    GS->Phase = ESPPhase::Waiting;
    GS->RoundSeconds = 180.f;
    GS->HackProgress = 0.f;
    ResultSeconds = 0.f;
    for (FConstPlayerControllerIterator It=GetWorld()->GetPlayerControllerIterator(); It; ++It)
        if (APlayerController* PC = It->Get())
            if (PC != Exclude) Respawn(PC);
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
    Super::DrawHUD();
    if (!Canvas || !PlayerOwner) return;
    const ASPGameState* GS = GetWorld()->GetGameState<ASPGameState>();
    const ASPCharacter* Pawn = Cast<ASPCharacter>(PlayerOwner->GetPawn());
    if (!GS || !Pawn) return;
    LastDrawTime=GetWorld()->GetTimeSeconds();
    const FLinearColor White = FLinearColor::White;
    const FLinearColor Accent = Pawn->IsSpy() ? FLinearColor(.2f,.75f,1.f) : FLinearColor(1.f,.6f,.2f);
    const float Scale=FMath::Min(Canvas->ClipX/900.f,Canvas->ClipY/500.f);
    auto Text=[this,Scale](const FString& Value,FLinearColor Color,float X,float Y)
    {DrawText(Value,Color,X*Scale,Y*Scale,nullptr,Scale);};
    DrawRect(FLinearColor(0,0,0,.7f),16*Scale,16*Scale,760*Scale,145*Scale);
    Text(Pawn->IsSpy() ? TEXT("SPY | THIRD PERSON") : TEXT("MERC | FIRST PERSON"), Accent, 28,26);
    FString Status;
    const ASPPlayerController* PC=Cast<ASPPlayerController>(PlayerOwner);
    const bool Pad=PC && PC->UsingGamepad();
    if (GS->bPractice) Status = Pad?TEXT("SOLO PRACTICE | D-pad Right swaps role | Scores disabled"):TEXT("SOLO PRACTICE | Tab swaps role | Scores disabled");
    else if (GS->Phase == ESPPhase::Waiting)
        Status = FString::Printf(TEXT("Waiting for 4 players | Spies %d/2 | Mercs %d/2"), GS->Spies, GS->Mercs);
    else if (GS->Phase == ESPPhase::SpiesWin) Status = TEXT("SPIES WIN | Restarting in 8 seconds");
    else if (GS->Phase == ESPPhase::MercsWin) Status = TEXT("MERCS WIN | Restarting in 8 seconds");
    else Status = FString::Printf(TEXT("Time %d:%02d | Terminal hacked %d%% | Health %d"),
        FMath::CeilToInt(GS->RoundSeconds)/60, FMath::CeilToInt(GS->RoundSeconds)%60,
        FMath::RoundToInt(GS->HackProgress*100), FMath::RoundToInt(Pawn->Health));
    Text(Status, White,28,52);
    Text(Pad?TEXT("LS move | RS look | B crouch / drop | A jump / vault / climb"):TEXT("WASD move | Mouse look | Ctrl crouch | Space jump / vault / climb"), White,28,78);
    Text(Pawn->IsSpy() ? (Pad?TEXT("Hold X hack | RT rear takedown | Y goggles up / down"):TEXT("E hack | Click rear takedown | N goggles up / down | Ctrl drop"))
        : (Pad?TEXT("RT shoot | Hold LT aim | Y flashlight | Defend terminal"):TEXT("Click shoot | Hold right mouse aim | F flashlight")), White,28,104);
    Text(TEXT("PROTOTYPE | Original game, placeholder character art"), White,28,130);
    if (Pawn->FeedbackUntil > GetWorld()->GetTimeSeconds()) Text(Pawn->Feedback,Accent,28,180);
    if (Pawn->Traversal()->Motion.State == ESPTraversal::Hanging) Text(Pad?TEXT("HANGING | A climb | B drop"):TEXT("HANGING | Space climb | Ctrl drop"),Accent,28,205);
    if (Pawn->NightVisionEnabled()) Text(TEXT("NIGHT VISION"),Accent,28,230);
    if (Pawn->Health <= 0.f) Text(TEXT("DOWN | Respawn after 5 seconds"), Accent,28,180);
    DrawLine(Canvas->ClipX/2-6,Canvas->ClipY/2,Canvas->ClipX/2+6,Canvas->ClipY/2,Accent);
    DrawLine(Canvas->ClipX/2,Canvas->ClipY/2-6,Canvas->ClipX/2,Canvas->ClipY/2+6,Accent);
}

void ASPPlayerController::ClientExercise_Implementation(const FString& Action)
{
#if WITH_EDITOR
    if (Action==TEXT("automation_on") || Action==TEXT("automation_off"))
    {bAutomatedInput=Action==TEXT("automation_on");if (PlayerInput) PlayerInput->FlushPressedKeys();return;}
    const TMap<FString,FKey> PadKeys={{TEXT("a"),EKeys::Gamepad_FaceButton_Bottom},{TEXT("b"),EKeys::Gamepad_FaceButton_Right},
        {TEXT("x"),EKeys::Gamepad_FaceButton_Left},{TEXT("y"),EKeys::Gamepad_FaceButton_Top},
        {TEXT("rt"),EKeys::Gamepad_RightTrigger},{TEXT("lt"),EKeys::Gamepad_LeftTrigger},
        {TEXT("role"),EKeys::Gamepad_DPad_Right},{TEXT("move"),EKeys::Gamepad_LeftY},{TEXT("drift"),EKeys::Gamepad_LeftY},{TEXT("look"),EKeys::Gamepad_RightX}};
    if (Action.StartsWith(TEXT("pad_")))
    {
        FString Button=Action.Mid(4);const bool Released=Button.RemoveFromEnd(TEXT("_up"));
        Button.RemoveFromEnd(TEXT("_down"));
        if (const FKey* Key=PadKeys.Find(Button))
            InputKey(FInputKeyEventArgs::CreateSimulated(*Key,Key->IsAnalog()?IE_Axis:(Released?IE_Released:IE_Pressed),Released?0.f:(Button==TEXT("drift")?.1f:1.f)));
        return;
    }
    if (ASPCharacter* Pawn=Cast<ASPCharacter>(GetPawn())) Pawn->Exercise(Action);
#endif
}
