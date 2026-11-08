#include "SPTraversalMovement.h"
#include "Prototype.h"
#include "SPWarehouse.h"
#include "EngineUtils.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/RootMotionSource.h"
#include "Net/UnrealNetwork.h"

USPTraversalMovement::USPTraversalMovement() { SetIsReplicatedByDefault(true); }
void USPTraversalMovement::ProcessLanded(const FHitResult& Hit,float RemainingTime,int32 Iterations)
{
    // ProcessLanded handles walkable head contacts before velocity is zeroed.
    if (IsFalling()) if (auto* Spy=Cast<ASPCharacter>(CharacterOwner)) Spy->TryDropKnockoutImpact(Hit,Velocity.Z);
    Super::ProcessLanded(Hit,RemainingTime,Iterations);
}
void USPTraversalMovement::HandleImpact(const FHitResult& Hit,float TimeSlice,const FVector& MoveDelta)
{
    // Glancing upper-capsule contacts can take the impact/slide path instead.
    if (IsFalling()) if (auto* Spy=Cast<ASPCharacter>(CharacterOwner)) Spy->TryDropKnockoutImpact(Hit,Velocity.Z);
    Super::HandleImpact(Hit,TimeSlice,MoveDelta);
}
float USPTraversalMovement::ServerTime() const
{
    const AGameStateBase* GS=GetWorld()->GetGameState();
    return GS ? GS->GetServerWorldTimeSeconds() : GetWorld()->GetTimeSeconds();
}
bool USPTraversalMovement::ClearAt(const FVector& Location) const
{
    FCollisionQueryParams Q(SCENE_QUERY_STAT(TraversalClearance), false, CharacterOwner);
    return !GetWorld()->OverlapBlockingTestByChannel(Location,FQuat::Identity,ECC_Pawn,
        FCollisionShape::MakeCapsule(35.f,88.f),Q);
}
void USPTraversalMovement::StartMotion(ESPTraversal State,const FVector& Target,float Duration)
{
    Motion.State=State;Motion.Start=UpdatedComponent->GetComponentLocation();Motion.Target=Target;
    Motion.ServerStart=ServerTime();Motion.Duration=Duration;++Motion.Revision;
    OnRep_Motion();CharacterOwner->ForceNetUpdate();
}
void USPTraversalMovement::OnRep_Motion()
{
    if (!CharacterOwner) return;
    if (Motion.State==ESPTraversal::Grounded)
    {
        RemoveRootMotionSource(TEXT("StealthTraversal"));
        SetMovementMode(MOVE_Falling);return;
    }
    if (IsOnRope() && !Motion.bVentCrouch && CharacterOwner->bIsCrouched)
    {SetMovementMode(MOVE_Walking);bWantsToCrouch=false;UnCrouch();if (CharacterOwner->GetLocalRole()==ROLE_AutonomousProxy) CharacterOwner->SetActorLocation(Motion.Start,false,nullptr,ETeleportType::TeleportPhysics);}
    if (Motion.bVentCrouch && !CharacterOwner->bIsCrouched)
    {
        SetMovementMode(MOVE_Walking);bWantsToCrouch=true;Crouch(false);
        // Autonomous owners do not receive normal bIsCrouched replication.
        if (CharacterOwner->GetLocalRole()==ROLE_AutonomousProxy) CharacterOwner->SetActorLocation(Motion.Start,false,nullptr,ETeleportType::TeleportPhysics);
    }
    SetMovementMode(MOVE_Flying);Velocity=FVector::ZeroVector;
    // Crouch writes the mesh offset directly. A stationary reach has no capsule
    // move to propagate it, so refresh now instead of dropping 46 cm until pull-up.
    if (Motion.bVentCrouch) CharacterOwner->GetMesh()->UpdateComponentToWorld();
    if (CharacterOwner->GetLocalRole()==ROLE_SimulatedProxy) return;
    RemoveRootMotionSource(TEXT("StealthTraversal"));
    if (Motion.Duration<=0) return;
    TSharedPtr<FRootMotionSource_MoveToForce> Source=MakeShared<FRootMotionSource_MoveToForce>();
    Source->InstanceName=TEXT("StealthTraversal");Source->Priority=1000;
    Source->AccumulateMode=ERootMotionAccumulateMode::Override;
    Source->StartLocation=Motion.Start;Source->TargetLocation=Motion.Target;
    Source->Duration=Motion.Duration;Source->bRestrictSpeedToExpected=true;
    Source->SetTime(FMath::Clamp(ServerTime()-Motion.ServerStart,0.f,Motion.Duration));
    if (IsOnRope())
    {Source->FinishVelocityParams.Mode=ERootMotionFinishVelocityMode::SetVelocity;Source->FinishVelocityParams.SetVelocity=FVector::ZeroVector;}
    SourceID=ApplyRootMotionSource(Source);
}
bool USPTraversalMovement::TryTraversal()
{
    ASPCharacter* Spy=Cast<ASPCharacter>(CharacterOwner);
    if (!Spy || !Spy->HasAuthority() || !Spy->IsSpy() || !Spy->IsRoundActive() || IsTraversing() || IsCrouching()) return false;
    const FVector Pos=Spy->GetActorLocation();
    const FVector Forward=FRotator(0,Spy->GetControlRotation().Yaw,0).Vector();
    FCollisionQueryParams Q(SCENE_QUERY_STAT(TraversalProbe),false,Spy);
    FHitResult Wall;
    if (!GetWorld()->LineTraceSingleByChannel(Wall,Pos-FVector(0,0,35),Pos-FVector(0,0,35)+Forward*Reach,ECC_Visibility,Q)) return false;
    UPrimitiveComponent* Surface=Wall.GetComponent();
    if (!Surface || !Surface->ComponentHasTag(TEXT("Traversal")) || Surface->Mobility!=EComponentMobility::Static || FMath::Abs(Wall.ImpactNormal.Z)>.2f) return false;
    FHitResult Top;
    const FVector Feet=Pos-FVector(0,0,Spy->GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
    const FVector TopProbe=Wall.ImpactPoint-Wall.ImpactNormal*15+FVector(0,0,MaxLedgeHeight+100);
    if (!GetWorld()->LineTraceSingleByChannel(Top,TopProbe,FVector(TopProbe.X,TopProbe.Y,Feet.Z+MinLedgeHeight),ECC_Visibility,Q)
        || Top.GetComponent()!=Surface || Top.ImpactNormal.Z<.9f) return false;
    const float Height=Top.ImpactPoint.Z-Feet.Z;
    if (Height<MinLedgeHeight || Height>MaxLedgeHeight) return false;
    StandOutside=FVector(Wall.ImpactPoint.X,Wall.ImpactPoint.Y,Top.ImpactPoint.Z+92)+Wall.ImpactNormal*55;
    StandInside=FVector(Wall.ImpactPoint.X,Wall.ImpactPoint.Y,Top.ImpactPoint.Z+92)-Wall.ImpactNormal*85;
    if (!ClearAt(StandOutside) || !ClearAt(StandInside)) return false;
    Ledge=Surface;Stage=0;StopMovementImmediately();
    Spy->SetActorRotation((-Wall.ImpactNormal).Rotation());
    if (Height<=115.f)
    {
        StandInside-=Wall.ImpactNormal*130;
        if (!ClearAt(StandInside)) return false;
        StartMotion(ESPTraversal::Vaulting,StandOutside,.35f);
    }
    else
    {
        const FVector Hang=StandOutside-FVector(0,0,155);
        if (!ClearAt(Hang)) return false;
        StartMotion(ESPTraversal::Hanging,Hang,.3f);
    }
    return true;
}
bool USPTraversalMovement::Climb()
{
    if (!CharacterOwner->HasAuthority() || Motion.State!=ESPTraversal::Hanging || Motion.Duration>0 || !ClearAt(StandOutside) || !ClearAt(StandInside)) return false;
    Stage=0;StartMotion(ESPTraversal::Climbing,StandOutside,.65f);return true;
}
void USPTraversalMovement::Drop()
{
    if (!CharacterOwner || !CharacterOwner->HasAuthority()) return;
    ActiveRope.Reset();RopeAxis=0;RopeStage=0;Motion.bVentCrouch=false;Motion.bEnteringVent=false;
    Ledge.Reset();Stage=0;StartMotion(ESPTraversal::Grounded,UpdatedComponent->GetComponentLocation(),0);
}
void USPTraversalMovement::TickComponent(float Delta,ELevelTick Tick,FActorComponentTickFunction* Function)
{
    Super::TickComponent(Delta,Tick,Function);
    if (!CharacterOwner || !CharacterOwner->HasAuthority() || !IsTraversing()) return;
    if (IsOnRope()) {TickRope();return;}
    ASPCharacter* Spy=Cast<ASPCharacter>(CharacterOwner);
    if (!Ledge.IsValid() || !Spy || Spy->Health<=0 || !Spy->IsRoundActive()) { Drop();return; }
    if (Motion.Duration<=0 || ServerTime()<Motion.ServerStart+Motion.Duration+.06f) return;
    if (FVector::Dist(Spy->GetActorLocation(),Motion.Target)>35.f) { Drop();return; }
    if (Motion.State==ESPTraversal::Hanging)
    {
        StartMotion(ESPTraversal::Hanging,Motion.Target,0);return;
    }
    if (Stage==0)
    {
        if (!ClearAt(StandInside)) { Drop();return; }
        Stage=1;StartMotion(Motion.State,StandInside,.55f);
    }
    else Drop();
}
void USPTraversalMovement::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(USPTraversalMovement,Motion);
}

bool USPTraversalMovement::CanCrouchInCurrentState() const
{
    return Super::CanCrouchInCurrentState() || (IsOnRope() && Motion.bVentCrouch);
}
void USPTraversalMovement::UpdateCharacterStateBeforeMovement(float DeltaSeconds)
{
    // In-flight saved moves may predate the replicated mantle. Traversal owns
    // capsule posture until it ends; stale input must not stand the spy up.
    if (IsOnRope()) bWantsToCrouch=Motion.bVentCrouch;
    Super::UpdateCharacterStateBeforeMovement(DeltaSeconds);
}
bool USPTraversalMovement::TryRope()
{
    ASPCharacter* Spy=Cast<ASPCharacter>(CharacterOwner);
    if (!Spy || !Spy->HasAuthority() || !Spy->IsSpy() || !Spy->IsRoundActive() || Spy->IsRestrained() || Spy->IsStunned() || IsTraversing()) return false;
    ASPRope* Closest=nullptr;float Best=180.f;bool FromTop=false;
    for (TActorIterator<ASPRope> It(GetWorld());It;++It)
    {
        const float D=FVector::Dist2D(Spy->GetActorLocation(),It->Bottom());
        // A capsule can straddle the lip while its center is just outside the
        // vent volume. Keep that supported edge eligible for a rope remount.
        const bool AtMouth=FVector::Dist2D(Spy->GetActorLocation(),It->Entry)<120.f;
        const bool Top=FMath::Abs(Spy->GetActorLocation().Z-(It->FloorHeight+44.f))<80.f && Spy->bIsCrouched && (Spy->IsInsideVent() || AtMouth);
        const bool Bottom=D<115.f && FMath::Abs(Spy->GetActorLocation().Z-It->Bottom().Z)<85.f;
        if (D<Best && (Top || Bottom)) {Best=D;Closest=*It;FromTop=Top;}
    }
    if (!Closest) return false;
    if (!FromTop && Spy->bIsCrouched) {bWantsToCrouch=false;UnCrouch();if (Spy->bIsCrouched) return false;}
    FCollisionQueryParams Q(SCENE_QUERY_STAT(RopeMount),false,Spy);FHitResult H;
    FVector Mount=FromTop?Closest->Top():Closest->Bottom();if (FromTop) Mount.Z=Closest->FloorHeight+44;
    if (GetWorld()->SweepSingleByChannel(H,Spy->GetActorLocation(),Mount,FQuat::Identity,ECC_Pawn,Spy->GetCapsuleComponent()->GetCollisionShape(),Q)) return false;
    ActiveRope=Closest;RopeAxis=0;RopeStage=FromTop?4:0;Motion.bVentCrouch=FromTop;Motion.bEnteringVent=false;Motion.RopeBaseZ=Closest->Bottom().Z;StopMovementImmediately();Spy->SetActorRotation(Closest->GetActorRotation());
    StartMotion(ESPTraversal::Rope,Mount,FromTop?.55f:.2f);Spy->ClientFeedback(TEXT("ROPE | LS up / down | B drop"));return true;
}
void USPTraversalMovement::SetRopeInput(float Axis)
{
    if (!CharacterOwner || !CharacterOwner->HasAuthority() || !IsOnRope() || !FMath::IsFinite(Axis)) return;
    RopeAxis=FMath::Clamp(Axis,-1.f,1.f);RopeInputAt=ServerTime();
}
void USPTraversalMovement::TickRope()
{
    ASPCharacter* Spy=Cast<ASPCharacter>(CharacterOwner);ASPRope* Rope=ActiveRope.Get();
    if (!Spy || !Rope || !Spy->IsSpy() || !Spy->IsRoundActive() || Spy->IsStunned() || Spy->IsRestrained()) {Drop();return;}
    if (Motion.Duration>0 && ServerTime()<Motion.ServerStart+Motion.Duration+.015f) return;
    if (Motion.Duration>0 && FVector::Dist(Spy->GetActorLocation(),Motion.Target)>40.f) {Drop();return;}
    if (RopeStage==4)
    {
        SetMovementMode(MOVE_Walking);bWantsToCrouch=false;UnCrouch();
        if (Spy->bIsCrouched) {Drop();return;}
        Motion.bVentCrouch=false;RopeStage=0;StartMotion(ESPTraversal::Rope,Rope->Top(),.6f);return;
    }
    if (Motion.bEnteringVent)
    {
        const FVector Outside=Rope->Bottom();const FVector Forward=Rope->GetActorForwardVector();
        if (RopeStage==10) {RopeStage=11;Motion.VentPhaseTime=.5f;FVector Target=Outside+Forward*25;Target.Z=Rope->FloorHeight+14;StartMotion(ESPTraversal::RopeExit,Target,.9f);return;}
        if (RopeStage==11) {RopeStage=12;Motion.VentPhaseTime=1.4f;FVector Target=Outside+Forward*25;Target.Z=Rope->FloorHeight+44;StartMotion(ESPTraversal::RopeExit,Target,.25f);return;}
        if (RopeStage==12) {RopeStage=13;Motion.VentPhaseTime=1.65f;FVector Target=Outside+Forward*100;Target.Z=Rope->FloorHeight+44;StartMotion(ESPTraversal::RopeExit,Target,.65f);return;}
        if (RopeStage==13) {RopeStage=14;Motion.VentPhaseTime=2.3f;StartMotion(ESPTraversal::RopeExit,Rope->Entry,.9f);return;}
        Drop();return;
    }
    RopeStage=1;
    if (RopeAxis>.1f && Spy->GetActorLocation().Z>=Rope->Top().Z-3.f)
    {
        // Shrink collision without changing the rendered hanging pose. The
        // authored mantle owns the entire reach / pull / knee / trailing-leg arc.
        SetMovementMode(MOVE_Walking);bWantsToCrouch=true;Crouch(false);
        if (!Spy->bIsCrouched) {Drop();return;}
        SetMovementMode(MOVE_Flying);Motion.bVentCrouch=true;Motion.bEnteringVent=true;Motion.VentStartedAt=ServerTime();Motion.VentPhaseTime=0;RopeStage=10;
        StartMotion(ESPTraversal::RopeExit,Spy->GetActorLocation(),.5f);return;
    }
    if (ServerTime()-RopeInputAt>.35f) RopeAxis=0;
    if (FMath::Abs(RopeAxis)<.1f)
    {if (Motion.Duration>0) StartMotion(ESPTraversal::Rope,Motion.Target,0);return;}
    FVector Target=Rope->Bottom();Target.Z=FMath::Clamp(Spy->GetActorLocation().Z+RopeAxis*RopeSpeed*.12f,Rope->Bottom().Z,Rope->Top().Z);
    if (FMath::Abs(Target.Z-Spy->GetActorLocation().Z)<1.f) {StartMotion(ESPTraversal::Rope,Spy->GetActorLocation(),0);return;}
    FCollisionQueryParams Q(SCENE_QUERY_STAT(RopeClimbClearance),false,Spy);FHitResult H;
    if (GetWorld()->SweepSingleByChannel(H,Spy->GetActorLocation(),Target,FQuat::Identity,ECC_Pawn,Spy->GetCapsuleComponent()->GetCollisionShape(),Q)) {Drop();return;}
    StartMotion(ESPTraversal::Rope,Target,.12f);
}
