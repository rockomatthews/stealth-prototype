#include "SPTraversalMovement.h"
#include "Prototype.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/RootMotionSource.h"
#include "Net/UnrealNetwork.h"

USPTraversalMovement::USPTraversalMovement() { SetIsReplicatedByDefault(true); }
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
    SetMovementMode(MOVE_Flying);Velocity=FVector::ZeroVector;
    if (CharacterOwner->GetLocalRole()==ROLE_SimulatedProxy) return;
    RemoveRootMotionSource(TEXT("StealthTraversal"));
    if (Motion.Duration<=0) return;
    TSharedPtr<FRootMotionSource_MoveToForce> Source=MakeShared<FRootMotionSource_MoveToForce>();
    Source->InstanceName=TEXT("StealthTraversal");Source->Priority=1000;
    Source->AccumulateMode=ERootMotionAccumulateMode::Override;
    Source->StartLocation=Motion.Start;Source->TargetLocation=Motion.Target;
    Source->Duration=Motion.Duration;Source->bRestrictSpeedToExpected=true;
    Source->SetTime(FMath::Clamp(ServerTime()-Motion.ServerStart,0.f,Motion.Duration));
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
    Ledge.Reset();Stage=0;StartMotion(ESPTraversal::Grounded,UpdatedComponent->GetComponentLocation(),0);
}
void USPTraversalMovement::TickComponent(float Delta,ELevelTick Tick,FActorComponentTickFunction* Function)
{
    Super::TickComponent(Delta,Tick,Function);
    if (!CharacterOwner || !CharacterOwner->HasAuthority() || !IsTraversing()) return;
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
