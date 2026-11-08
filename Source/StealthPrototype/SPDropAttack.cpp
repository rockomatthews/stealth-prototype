#include "Prototype.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Sound/SoundBase.h"

bool ASPCharacter::HasRecoveryShield() const
{
    return !IsSpy() && IsRoundActive() && RecoveryShield.Until>ServerNow();
}
bool ASPCharacter::IsGettingUp() const
{
    return HasRecoveryShield() && RecoveryShield.GetUpAt>0 && ServerNow()<RecoveryShield.GetUpAt+MercGetUpSeconds;
}
void ASPCharacter::MulticastRecoveryRepel_Implementation(FVector Impulse)
{
    if (HasAuthority() || IsLocallyControlled()) LaunchCharacter(Impulse,true,true);
}
void ASPCharacter::RepelRecoverySpy(ASPCharacter* Spy)
{
    if (!HasAuthority() || !HasRecoveryShield() || !Spy || !Spy->IsSpy() || Spy->Health<=0 || Spy->IsRestrained() || Spy->ServerNow()-Spy->LastRecoveryRepel<.6f) return;
    Spy->LastRecoveryRepel=ServerNow();
    FVector Away=(Spy->GetActorLocation()-GetActorLocation()).GetSafeNormal2D();
    if (Away.IsNearlyZero()) Away=-GetActorForwardVector();
    Spy->MulticastRecoveryRepel(Away*480.f+FVector(0,0,220.f));Spy->ForceNetUpdate();
    Spy->ClientFeedback(TEXT("RECOVERY SHIELD | Merc protected from grabs and drops"));
}

void ASPCharacter::OnRep_Knockout(FSPKnockout Previous)
{
    if (Knockout.bActive)
    {
        GetCharacterMovement()->StopMovementImmediately();GetCharacterMovement()->DisableMovement();
        GetCapsuleComponent()->SetCapsuleHalfHeight(34.f);
        SetActorLocation(Knockout.StandLocation-FVector(0,0,Knockout.HalfHeight-34.f),false,nullptr,ETeleportType::TeleportPhysics);
        GetMesh()->SetRelativeLocation(Knockout.MeshLocation+FVector(0,0,Knockout.HalfHeight-34.f));
        CacheInitialMeshOffset(GetMesh()->GetRelativeLocation(),GetMesh()->GetRelativeRotation());
        KnockoutHitBox->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        bAiming=false;bInteractHeld=false;ResetCameraView();
    }
    else if (Previous.bActive)
    {
        GetCapsuleComponent()->SetCapsuleHalfHeight(Previous.HalfHeight);
        SetActorLocation(Previous.StandLocation,false,nullptr,ETeleportType::TeleportPhysics);
        GetMesh()->SetRelativeLocation(Previous.MeshLocation);
        CacheInitialMeshOffset(GetMesh()->GetRelativeLocation(),GetMesh()->GetRelativeRotation());
        KnockoutHitBox->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        if (Health>0) GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    }
}
void ASPCharacter::BeginDropKnockout(ASPCharacter* Spy)
{
    if (!HasAuthority() || IsSpy() || !IsRoundActive() || IsKnockedOut() || HasRecoveryShield() || IsRestrained() || !Spy || !Spy->IsSpy()) return;
    EndGrab();BeforeKnockoutWeapon=WeaponMode();SetWeapon(ESPWeapon::Hands);bFlashlight=false;
    FSPKnockout Previous=Knockout;Knockout.bActive=true;Knockout.StartedAt=ServerNow();Knockout.Until=ServerNow()+FMath::Clamp(DropKnockoutSeconds,1.f,15.f);
    Knockout.StandLocation=GetActorLocation();Knockout.HalfHeight=GetCapsuleComponent()->GetScaledCapsuleHalfHeight();Knockout.MeshLocation=GetMesh()->GetRelativeLocation();OnRep_Knockout(Previous);ForceNetUpdate();
    ClientFeedback(TEXT("KNOCKED OUT BY DROP ATTACK"));Spy->ClientFeedback(TEXT("DROP KNOCKOUT"));
    Spy->MulticastSound(LoadObject<USoundBase>(nullptr,TEXT("/Game/Characters/Actions/DropImpact.DropImpact")),GetActorLocation());
}
void ASPCharacter::ClearKnockout()
{
    if (!HasAuthority()) return;
    if (Health<=0 || IsSpy()) {RecoveryShield=FSPRecoveryShield();ForceNetUpdate();}
    if (!Knockout.bActive) return;
    if (Health>0 && !IsSpy())
    {
        if (RecoveryShield.StartedAt<=Knockout.StartedAt) RecoveryShield.StartedAt=ServerNow();
        RecoveryShield.CapsuleRise=Knockout.HalfHeight-34.f;RecoveryShield.GetUpAt=ServerNow();RecoveryShield.Until=ServerNow()+FMath::Max(RecoveryShieldSeconds,MercGetUpSeconds+1.f);
        ClientFeedback(TEXT("RECOVERY SHIELD | Get up and reposition"));
    }
    const FSPKnockout Previous=Knockout;Knockout=FSPKnockout();OnRep_Knockout(Previous);
    if (Health>0 && WeaponMode()!=BeforeKnockoutWeapon) SetWeapon(BeforeKnockoutWeapon);ForceNetUpdate();
}
void ASPCharacter::UpdateDropAttack()
{
    if (!HasAuthority()) return;
    if (Knockout.bActive && Health>0 && ServerNow()>=Knockout.Until-MercGetUpSeconds)
    {
        if (RecoveryShield.StartedAt<=Knockout.StartedAt)
        {RecoveryShield.StartedAt=ServerNow();RecoveryShield.Until=ServerNow()+RecoveryShieldSeconds;RecoveryShield.GetUpAt=0;ForceNetUpdate();}
        if (RecoveryShield.Until<ServerNow()+1.f) {RecoveryShield.Until=ServerNow()+RecoveryShieldSeconds;ForceNetUpdate();}
        // Push campers out of the standing capsule before testing get-up space.
        for (TActorIterator<ASPCharacter> It(GetWorld());It;++It)
        {
            if (!It->IsSpy() || It->Health<=0) continue;
            const FVector P=It->GetActorLocation(),S=Knockout.StandLocation;
            if (FVector::Dist2D(P,S)<95.f && P.Z+It->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()>S.Z-Knockout.HalfHeight && P.Z-It->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()<S.Z+Knockout.HalfHeight) RepelRecoverySpy(*It);
        }
    }
    if (Knockout.bActive && Health>0 && ServerNow()>=Knockout.Until)
    {
        FCollisionQueryParams Q(SCENE_QUERY_STAT(KnockoutRecovery),false,this);
        if (!GetWorld()->OverlapBlockingTestByChannel(Knockout.StandLocation,FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(GetCapsuleComponent()->GetScaledCapsuleRadius(),Knockout.HalfHeight),Q)) ClearKnockout();
        else {Knockout.Until=ServerNow()+.25f;ForceNetUpdate();}
    }
}

bool ASPCharacter::TryDropKnockoutImpact(const FHitResult& Hit,float FallingSpeed)
{
    // Only real server movement collisions count. There is no client target RPC,
    // once-per-render-frame height window, or trace redirected toward a merc.
    if (!HasAuthority() || !IsSpy() || !IsRoundActive() || IsStunned() || IsRestrained()
        || Traversal()->IsTraversing() || !GetCharacterMovement()->IsFalling()
        || !FMath::IsFinite(FallingSpeed) || FallingSpeed>=-220.f || ServerNow()-LastDropAttack<=1.f
        || !Hit.bBlockingHit || Hit.ImpactNormal.Z<.5f) return false;
    ASPCharacter* Merc=Cast<ASPCharacter>(Hit.GetActor());
    if (!Merc || Merc==this || Merc->IsSpy() || !Merc->IsRoundActive() || Merc->IsKnockedOut()
        || Merc->IsRestrained() || Hit.GetComponent()!=Merc->GetCapsuleComponent()) return false;
    const float Top=Merc->GetActorLocation().Z+Merc->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    if (GetActorLocation().Z<=Top || Hit.ImpactPoint.Z<Top-Merc->GetCapsuleComponent()->GetScaledCapsuleRadius()
        || FVector::Dist2D(Hit.Location,Merc->GetActorLocation())>48.f) return false;
    if (Merc->HasRecoveryShield()) {if (ServerNow()-LastRecoveryRepel>=.6f) ++Merc->RecoveryDropBlocks;Merc->RepelRecoverySpy(this);return false;}
    Merc->BeginDropKnockout(this);
    if (!Merc->IsKnockedOut()) return false;
    LastDropAttack=ServerNow();++DropKnockoutCount;
    FVector Away=(GetActorLocation()-Merc->GetActorLocation()).GetSafeNormal2D();
    if (Away.IsNearlyZero()) Away=-GetActorForwardVector();
    LaunchCharacter(Away*110.f+FVector(0,0,120.f),true,true);
    return true;
}
