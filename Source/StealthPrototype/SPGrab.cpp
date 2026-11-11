#include "Prototype.h"
#include "SPHandContacts.h"
#include "Components/CapsuleComponent.h"
#include "Components/SphereComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "EngineUtils.h"
#include "Engine/DamageEvents.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Engine/StaticMesh.h"
#include "SPBlast.h"

bool ASPCharacter::TryBeginGrab()
{
    if (!HasAuthority() || !IsSpy() || !IsRoundActive() || BlocksGrabCombat() || IsStunned() || Traversal()->IsTraversing() || ServerViewedCamera.IsValid() || WeaponMode()!=ESPWeapon::Hands || !GetCharacterMovement()->IsMovingOnGround()) return false;
    const FVector Direction=FRotator(0,GetBaseAimRotation().Yaw,0).Vector();
    const FVector Start=GetActorLocation()+FVector(0,0,35);
    FHitResult Hit;FCollisionQueryParams Query(SCENE_QUERY_STAT(RearGrab),false,this);
    GetWorld()->SweepSingleByChannel(Hit,Start,Start+Direction*150.f,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(20),Query);
    ASPCharacter* Target=Cast<ASPCharacter>(Hit.GetActor());
    if (!Target || Target->bIsCrouched || FVector::DistSquared(Target->GetActorLocation(),GetActorLocation())>FMath::Square(150.f) || !Target->GetPlayerState() || !Target->GetController() || Target->IsSpy() || !Target->IsRoundActive() || Target->IsRestrained() || Target->Traversal()->IsTraversing() || !Target->GetCharacterMovement()->IsMovingOnGround() || FMath::Abs(Target->GetActorLocation().Z-GetActorLocation().Z)>60) return false;
    const FVector ToSpy=(GetActorLocation()-Target->GetActorLocation()).GetSafeNormal2D();
    if (FVector::DotProduct(Target->GetActorForwardVector(),ToSpy)>-.6f) {ClientFeedback(TEXT("Grab requires a rear approach"));return false;}
    if (Target->HasRecoveryShield()) {++Target->RecoveryGrabBlocks;ClientFeedback(TEXT("RECOVERY SHIELD | Merc cannot be grabbed yet"));return false;}
    if (bIsCrouched)
    {
        GetCharacterMovement()->bWantsToCrouch=false;GetCharacterMovement()->UnCrouch();
        if (bIsCrouched) return false; // Insufficient headroom: do not freeze below the floor.
    }
    const float Gap=40.f;
    const FVector Hold=Target->GetActorLocation()-Target->GetActorForwardVector()*Gap;
    Query.AddIgnoredActor(Target);
    FHitResult Block;
    if (GetWorld()->SweepSingleByChannel(Block,GetActorLocation(),Hold,FQuat::Identity,ECC_Pawn,GetCapsuleComponent()->GetCollisionShape(),Query)) return false;
    ASPGameState* GS=GetWorld()->GetGameState<ASPGameState>();
    const uint32 Token=GS->NextGrabToken++;
    const FSPGrabState Previous=Grab,TargetPrevious=Target->Grab;
    Grab.Partner=Target;Grab.bCaptor=true;Grab.Token=Token;Grab.StartedAt=ServerNow();
    Target->Grab.Partner=this;Target->Grab.bCaptor=false;Target->Grab.Token=Token;Target->Grab.StartedAt=Grab.StartedAt;
    WeaponBeforeGrab=WeaponMode();Target->WeaponBeforeGrab=Target->WeaponMode();
    if (WeaponMode()!=ESPWeapon::Hands) SetWeapon(ESPWeapon::Hands);
    if (Target->WeaponMode()!=ESPWeapon::Carbine) Target->SetWeapon(ESPWeapon::Carbine);
    SetActorLocation(Hold,false,nullptr,ETeleportType::TeleportPhysics);SetActorRotation(Target->GetActorRotation());
    SafeGrabPosition=GetActorLocation();SafeGrabFacing=GetActorRotation();
    OnRep_Grab(Previous);Target->OnRep_Grab(TargetPrevious);ForceNetUpdate();Target->ForceNetUpdate();
    if (ASPPlayerController* PC=Cast<ASPPlayerController>(Controller))
    {
        PC->SetControlRotation(Target->GetActorRotation());PC->ClientGrabPose(GetActorLocation(),Target->GetActorRotation());
        PC->ClientVoicePair(Target->GetPlayerState()->GetPlayerId(),Token);
    }
    if (ASPPlayerController* PC=Cast<ASPPlayerController>(Target->Controller)) PC->ClientVoicePair(GetPlayerState()->GetPlayerId(),Token);
    ClientFeedback(TEXT("Holding merc | Move slowly / turn | Tap RT snap | Hold RT finisher"));
    Target->ClientFeedback(TEXT("GRABBED | Voice link open with captor"));return true;
}
void ASPPlayerController::ClientGrabPose_Implementation(FVector Position,FRotator Facing)
{
    if (ASPCharacter* Pawn=Cast<ASPCharacter>(GetPawn()))
    {
        // bIsCrouched is normally simulated-proxy only. Normalize the autonomous
        // owner's capsule as well, then apply the server's validated hold location.
        Pawn->GetCharacterMovement()->bWantsToCrouch=false;
        Pawn->GetCharacterMovement()->UnCrouch();
        Pawn->GetCharacterMovement()->StopMovementImmediately();
        Pawn->SetActorLocation(Position,false,nullptr,ETeleportType::TeleportPhysics);
        Pawn->SetActorRotation(Facing);SetControlRotation(Facing);
    }
}
void ASPCharacter::OnRep_Grab(FSPGrabState Previous)
{
    bAiming=false;bInteractHeld=false;ResetCameraView();
    if (!IsRestrained()) {HeldPoseToken=0;FinishPressedAt=-1;}
    if (Previous.Partner && Previous.Partner!=Grab.Partner)
    {
        // Only the authoritative five-second completion sets ChokeExitAt.
        // Inferring success from elapsed time here incorrectly played a dismount
        // when rescue damage interrupted the choke immediately before completion.
        ChokeExitPartner=Previous.Partner; // Ignore only until the capsules separate.
    }
    if (IsRestrained())
    {
        GetCapsuleComponent()->IgnoreActorWhenMoving(Grab.Partner,true);
        if ((IsCaptor() && !IsFinishing()) || IsChokeVictim()) GetCharacterMovement()->SetMovementMode(MOVE_Walking);
        else {GetCharacterMovement()->StopMovementImmediately();GetCharacterMovement()->DisableMovement();}
    }
    else if (Previous.Token && Health>0) GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    if (!IsRestrained() && Previous.Token)
        if (ASPPlayerController* PC=Cast<ASPPlayerController>(Controller))
            if (PC->IsLocalController() && PC->Voice->PairToken==Previous.Token) PC->Voice->SetPair(-1,0);
}
void ASPCharacter::EndGrab()
{
    if (!HasAuthority() || !IsRestrained()) return;
    FinishPressedAt=-1;
    ASPCharacter* Partner=Grab.Partner;const uint32 Token=Grab.Token;
    const FSPGrabState Previous=Grab;Grab=FSPGrabState();OnRep_Grab(Previous);if (Previous.Finisher!=ESPFinisher::BackChoke && Health>0 && WeaponMode()!=WeaponBeforeGrab) SetWeapon(WeaponBeforeGrab);ForceNetUpdate();
    if (ASPPlayerController* PC=Cast<ASPPlayerController>(Controller)) PC->ClientVoicePair(-1,0);
    if (IsValid(Partner) && Partner->Grab.Token==Token && Partner->Grab.Partner==this)
    {
        const FSPGrabState Other=Partner->Grab;Partner->Grab=FSPGrabState();Partner->OnRep_Grab(Other);if (Other.Finisher!=ESPFinisher::BackChoke && Partner->Health>0 && Partner->WeaponMode()!=Partner->WeaponBeforeGrab) Partner->SetWeapon(Partner->WeaponBeforeGrab);Partner->ForceNetUpdate();
        if (ASPPlayerController* PC=Cast<ASPPlayerController>(Partner->Controller)) PC->ClientVoicePair(-1,0);
    }
}
void ASPCharacter::ValidateGrab()
{
    if (!HasAuthority() || !IsRestrained()) return;
    const ASPCharacter* Partner=Grab.Partner;
    if (!IsValid(Partner) || !IsRoundActive() || !Partner->IsRoundActive() || (Grab.bCaptor?IsStunned():Partner->IsStunned()) || Partner->Grab.Partner!=this || Partner->Grab.Token!=Grab.Token || FVector::DistSquared(GetActorLocation(),Partner->GetActorLocation())>FMath::Square(IsFinishing()?260.f:180.f)) EndGrab();
}
void ASPCharacter::ServerReleaseGrab_Implementation() {if (IsCaptor()) EndGrab();}
void ASPCharacter::ServerFinishGrab_Implementation() {BeginFinisher(false);}
void ASPCharacter::ServerFinishInput_Implementation(bool Pressed)
{
    ValidateGrab();
    if (!IsCaptor() || IsFinishing() || !IsRoundActive() || IsStunned()) return;
    if (Pressed) {if (FinishPressedAt<0) FinishPressedAt=ServerNow();}
    else if (FinishPressedAt>=0)
    {
        const bool Extended=ServerNow()-FinishPressedAt>=FinishHoldSeconds;
        FinishPressedAt=-1;BeginFinisher(Extended);
    }
}
void ASPCharacter::BeginFinisher(bool Extended)
{
    ValidateGrab();
    if (!IsCaptor() || IsFinishing() || !IsRoundActive() || IsStunned()) return;
    ASPCharacter* Victim=Grab.Partner;
    const ESPFinisher Kind=!Extended?ESPFinisher::NeckSnap:(Victim->MercGrenades>0?ESPFinisher::Grenade:ESPFinisher::BackChoke);
    // Reserve a clear capsule corridor before committing to the shove or mount.
    FCollisionQueryParams Q(SCENE_QUERY_STAT(FinishClearance),false,this);Q.AddIgnoredActor(Victim);
    FHitResult Hit;
    const float Travel=Kind==ESPFinisher::Grenade?145.f:0.f;
    const FVector End=Victim->GetActorLocation()+GetActorForwardVector()*Travel;
    if (GetWorld()->SweepSingleByChannel(Hit,Victim->GetActorLocation(),End,FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(Victim->GetCapsuleComponent()->GetScaledCapsuleRadius(),Victim->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()),Q))
    {ClientFeedback(TEXT("Not enough space for this finisher"));FinishPressedAt=-1;return;}
    FHitResult Floor;
    if (!GetWorld()->LineTraceSingleByChannel(Floor,End,End-FVector(0,0,130),ECC_Pawn,Q) || Floor.ImpactNormal.Z<.7f)
    {ClientFeedback(TEXT("Finisher needs solid ground"));FinishPressedAt=-1;return;}
    FinishPressedAt=-1;bFinishSpentGrenade=false;FinishOrigin=GetActorLocation();
    Grab.Finisher=Victim->Grab.Finisher=Kind;Grab.FinishStartedAt=Victim->Grab.FinishStartedAt=ServerNow();
    if (Kind==ESPFinisher::BackChoke && Victim->WeaponMode()!=ESPWeapon::Carbine) Victim->SetWeapon(ESPWeapon::Carbine);
    OnRep_Grab(Grab);Victim->OnRep_Grab(Victim->Grab);ForceNetUpdate();Victim->ForceNetUpdate();
    ClientFeedback(Kind==ESPFinisher::Grenade?TEXT("GRENADE PLANT | Shove then move away from the live grenade"):Kind==ESPFinisher::BackChoke?TEXT("BACK CHOKE | Hold on for five seconds"):TEXT("NECK SNAP"));
}
void ASPPlayerController::ClientHeldPose_Implementation(FVector Position,FRotator Facing,uint32 Token)
{
    if (ASPCharacter* P=Cast<ASPCharacter>(GetPawn()))
        if (P->Grab.Token==Token && P->BlocksGrabInput())
        {P->HeldTarget=Position;P->HeldFacing=Facing;P->HeldPoseToken=Token;}
}
void ASPCharacter::UpdateGrab(float Delta)
{
    if (ChokeExitPartner.IsValid() && !IsChokeExiting())
    {
        ASPCharacter* Other=ChokeExitPartner.Get();
        const bool Separated=FVector::Dist2D(GetActorLocation(),Other->GetActorLocation())>GetCapsuleComponent()->GetScaledCapsuleRadius()+Other->GetCapsuleComponent()->GetScaledCapsuleRadius()+2.f
            || FMath::Abs(GetActorLocation().Z-Other->GetActorLocation().Z)>GetCapsuleComponent()->GetScaledCapsuleHalfHeight()+Other->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
        if (Separated || Health<=0 || Other->Health<=0)
        {GetCapsuleComponent()->IgnoreActorWhenMoving(Other,false);ChokeExitPartner.Reset();}
    }
    if (!HasAuthority())
    {
        if (IsLocallyControlled() && IsRestrained() && BlocksGrabInput() && HeldPoseToken==Grab.Token)
        {
            SetActorLocationAndRotation(FMath::VInterpTo(GetActorLocation(),HeldTarget,Delta,25.f),FMath::RInterpTo(GetActorRotation(),HeldFacing,Delta,20.f),false,nullptr,ETeleportType::TeleportPhysics);
            if (Controller) Controller->SetControlRotation(GetActorRotation());
        }
        return;
    }
    if (!IsCaptor()) return;
    ASPCharacter* Victim=Grab.Partner;
    if (!IsValid(Victim)) return;
    if (FinishPressedAt>=0 && ServerNow()-FinishPressedAt>=FinishHoldSeconds) BeginFinisher(true);
    if (Grab.Finisher==ESPFinisher::BackChoke)
    {
        // The merc remains an ordinary predicted CharacterMovement pawn. Only
        // the rider follows; never overwrite the merc owner's aim or movement.
        const float T=ServerNow()-Grab.FinishStartedAt;
        const FRotator Facing(0,Victim->GetActorRotation().Yaw,0);
        const float Gap=40.f;
        const FVector Desired=Victim->GetActorLocation()-Facing.Vector()*Gap;
        FHitResult Hit;SetActorLocationAndRotation(Desired,Facing,true,&Hit);
        if (Hit.bBlockingHit) {EndGrab();return;}
        HeldPoseClock+=Delta;
        if (HeldPoseClock>=.05f)
        {
            HeldPoseClock=0;ForceNetUpdate();
            if (ASPPlayerController* PC=Cast<ASPPlayerController>(Controller)) PC->ClientHeldPose(Desired,Facing,Grab.Token);
        }
        if (T>=5.f)
        {
            ChokeExitAt=ServerNow();ForceNetUpdate();EndGrab();
            Victim->ChokeDeathAt=ServerNow();
            FDamageEvent Event;Victim->TakeDamage(100.f,Event,Controller,this);Victim->ForceNetUpdate();
            ClientFeedback(TEXT("STRANGULATION"));Victim->ClientFeedback(TEXT("STRANGLED"));
        }
        return;
    }
    const float Gap=40.f;
    FRotator Facing(0,IsFinishing()?SafeGrabFacing.Yaw:GetBaseAimRotation().Yaw,0);
    const float Elapsed=ServerNow()-Grab.FinishStartedAt;
    FVector Desired=GetActorLocation()+Facing.Vector()*Gap;
    if (IsFinishing())
    {
        FVector SpyPosition=FinishOrigin;
        FHitResult SpyHit;SetActorLocation(SpyPosition,true,&SpyHit);
        if (SpyHit.bBlockingHit) {EndGrab();return;} // Static obstruction or another player can interrupt the step.
        Desired=FinishOrigin+Facing.Vector()*Gap;
        if (Grab.Finisher==ESPFinisher::Grenade) Desired+=Facing.Vector()*145.f*FMath::Clamp((Elapsed-2.2f)/.6f,0.f,1.f);
    }
    FCollisionQueryParams Q(SCENE_QUERY_STAT(DragClearance),false,this);Q.AddIgnoredActor(Victim);
    FHitResult Hit,Floor;
    bool Blocked=GetWorld()->SweepSingleByChannel(Hit,Victim->GetActorLocation(),Desired,FQuat::Identity,ECC_Pawn,Victim->GetCapsuleComponent()->GetCollisionShape(),Q);
    Blocked|=!GetWorld()->LineTraceSingleByChannel(Floor,Desired,Desired-FVector(0,0,130),ECC_Pawn,Q) || Floor.ImpactNormal.Z<.7f;
    if (Blocked)
    {
        if (IsFinishing()) {EndGrab();return;}
        SetActorLocationAndRotation(SafeGrabPosition,SafeGrabFacing,false,nullptr,ETeleportType::TeleportPhysics);
        if (ASPPlayerController* PC=Cast<ASPPlayerController>(Controller)) PC->ClientGrabPose(SafeGrabPosition,SafeGrabFacing);
        return;
    }
    SetActorRotation(Facing);Victim->SetActorLocationAndRotation(Desired,Facing,false,nullptr,ETeleportType::TeleportPhysics);
    SafeGrabPosition=GetActorLocation();SafeGrabFacing=Facing;
    if (Victim->Controller) Victim->Controller->SetControlRotation(Facing);
    HeldPoseClock+=Delta;
    if (HeldPoseClock>=.05f)
    {
        HeldPoseClock=0;Victim->ForceNetUpdate();
        if (ASPPlayerController* PC=Cast<ASPPlayerController>(Victim->Controller)) PC->ClientHeldPose(Desired,Facing,Grab.Token);
        if (IsFinishing()) if (ASPPlayerController* PC=Cast<ASPPlayerController>(Controller)) PC->ClientHeldPose(GetActorLocation(),Facing,Grab.Token);
    }
    if (!IsFinishing()) return;
    if (Grab.Finisher==ESPFinisher::Grenade && Elapsed>=.55f && !bFinishSpentGrenade)
    {
        if (Victim->MercGrenades<=0) {EndGrab();return;}
        FActorSpawnParameters Params;Params.Owner=this;Params.Instigator=this;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        ASPGrabGrenade* G=GetWorld()->SpawnActor<ASPGrabGrenade>(GetActorLocation(),Facing,Params);
        if (!G) {EndGrab();return;}
        --Victim->MercGrenades;Victim->ForceNetUpdate();bFinishSpentGrenade=true;
        G->Victim=Victim;G->Captor=this;G->ArmedAt=Grab.FinishStartedAt+1.05f;G->Epoch=GetWorld()->GetGameState<ASPGameState>()->VoiceEpoch;G->ForceNetUpdate();
    }
    const float Duration=Grab.Finisher==ESPFinisher::NeckSnap?.85f:2.8f;
    if (Elapsed>=Duration)
    {
        const bool Explosive=Grab.Finisher==ESPFinisher::Grenade;
        EndGrab();
        if (!Explosive) {FDamageEvent Event;Victim->TakeDamage(100,Event,Controller,this);}
    }
}
void ASPCharacter::ToggleVoiceMute() {if (ASPPlayerController* PC=Cast<ASPPlayerController>(Controller)) PC->Voice->ToggleMute();}

void ASPCharacter::ThrowMercGrenade()
{
    if (!HasAuthority() || IsSpy() || !IsRoundActive() || !Controller || BlocksGrabCombat() || IsStunned() || Traversal()->IsTraversing() || IsThrowingGrenade()) return;
    if (MercGrenades<=0) {ClientFeedback(TEXT("Grenades empty"));return;}
    if (ServerNow()-LastGrenadeThrowAt<GrenadeThrowCooldown) return;
    FVector Eye;FRotator Aim;GetActorEyesViewPoint(Eye,Aim);FHitResult Hit;
    FCollisionQueryParams Q(SCENE_QUERY_STAT(ThrowWindupClearance),false,this);if (IsChokeVictim()) Q.AddIgnoredActor(Grab.Partner);
    const FVector Release=Eye+Aim.Vector()*55.f+FRotationMatrix(Aim).GetUnitAxis(EAxis::Y)*12.f-FVector(0,0,12.f);
    if (GetWorld()->SweepSingleByChannel(Hit,Eye,Release,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(5.f),Q)) {ClientFeedback(TEXT("Move away from cover to throw"));return;}
    ThrowStartedAt=LastGrenadeThrowAt=ServerNow();bThrowPending=true;bAiming=false;ForceNetUpdate();
}
void ASPCharacter::UpdateGrenadeThrow()
{
    if (!HasAuthority() || !bThrowPending) return;
    if (IsSpy() || !IsRoundActive() || BlocksGrabCombat() || IsStunned() || Traversal()->IsTraversing())
    {bThrowPending=false;ThrowStartedAt=-10;ForceNetUpdate();return;}
    if (ServerNow()-ThrowStartedAt>=.42f) {bThrowPending=false;ReleaseMercGrenade();}
}
void ASPCharacter::ReleaseMercGrenade()
{
    if (!HasAuthority() || IsSpy() || !IsRoundActive() || !Controller || BlocksGrabCombat() || IsStunned() || Traversal()->IsTraversing()) return;
    if (MercGrenades<=0) {ClientFeedback(TEXT("Grenades empty"));return;}
    FVector Eye;FRotator Aim;GetActorEyesViewPoint(Eye,Aim);
    const FVector Release=Eye+Aim.Vector()*55.f+FRotationMatrix(Aim).GetUnitAxis(EAxis::Y)*12.f-FVector(0,0,12.f);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(GrenadeRelease),false,this);if (IsChokeVictim()) Query.AddIgnoredActor(Grab.Partner);FHitResult Hit;
    if (GetWorld()->SweepSingleByChannel(Hit,Eye,Release,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(5.f),Query) ||
        GetWorld()->SweepSingleByChannel(Hit,GetActorLocation()+FVector(0,0,30),Release,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(5.f),Query))
    {ClientFeedback(TEXT("Move away from cover to throw"));return;}
    FActorSpawnParameters Params;Params.Owner=this;Params.Instigator=this;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ASPGrabGrenade* Grenade=GetWorld()->SpawnActor<ASPGrabGrenade>(Release,Aim,Params);
    if (!Grenade) return;
    Grenade->Captor=this;Grenade->ArmedAt=ServerNow();Grenade->Epoch=GetWorld()->GetGameState<ASPGameState>()->VoiceEpoch;
    if (IsChokeVictim()) Grenade->Collision->IgnoreActorWhenMoving(Grab.Partner,true);
    Grenade->Launch(Aim.Vector()*FMath::Clamp(GrenadeThrowSpeed,100.f,2000.f)+FVector(0,0,180.f)+GetVelocity()*.3f);
    --MercGrenades;LastGrenadeThrowAt=ServerNow();ForceNetUpdate();Grenade->ForceNetUpdate();
    ClientFeedback(FString::Printf(TEXT("Grenade thrown | %d remaining"),MercGrenades));
}

ASPGrabGrenade::ASPGrabGrenade()
{
    bReplicates=true;SetReplicateMovement(true);PrimaryActorTick.bCanEverTick=true;
    Collision=CreateDefaultSubobject<USphereComponent>(TEXT("GrenadeCollision"));RootComponent=Collision;
    Collision->InitSphereRadius(4.f);Collision->SetCollisionProfileName(TEXT("BlockAllDynamic"));Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Projectile=CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("GrenadeFlight"));Projectile->UpdatedComponent=Collision;
    Projectile->bAutoActivate=false;Projectile->bShouldBounce=true;Projectile->Bounciness=.45f;Projectile->Friction=.35f;
    Projectile->OnProjectileBounce.AddDynamic(this,&ASPGrabGrenade::OnBounce);
    Projectile->ProjectileGravityScale=1.f;Projectile->MaxSpeed=2400.f;Projectile->bForceSubStepping=true;
    Housing=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Grenade"));Housing->SetupAttachment(Collision);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    Housing->SetStaticMesh(Sphere.Object);Housing->SetWorldScale3D(FVector(.055f,.055f,.08f));Housing->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Lever=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SafetyLever"));Lever->SetupAttachment(Housing);
    SafetyPin=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SafetyPin"));SafetyPin->SetupAttachment(Housing);SafetyPin->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SPBlast::LoadAssets(this);
    Lever->SetStaticMesh(Cube.Object);Lever->SetRelativeLocation(FVector(0,0,40));Lever->SetRelativeScale3D(FVector(.3f,.3f,.3f));Lever->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}
void ASPGrabGrenade::OnBounce(const FHitResult& Impact,const FVector& Velocity) {if (HasAuthority()) ++BounceCount;}
void ASPGrabGrenade::Launch(const FVector& Velocity)
{
    if (!HasAuthority()) return;
    bThrown=true;bDetached=true;SafetyPin->SetVisibility(false);
    Collision->IgnoreActorWhenMoving(GetInstigator(),true);Collision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Projectile->Velocity=Velocity;Projectile->Activate();
}
void ASPGrabGrenade::BeginPlay()
{
    Super::BeginPlay();
    if (!DustMaterial) DustMaterial=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Characters/Grab/Blast/M_BlastDustSoft.M_BlastDustSoft"));
    if (UStaticMesh* Mesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Characters/Grab/SM_Grenade.SM_Grenade"))) {Housing->SetStaticMesh(Mesh);Housing->SetWorldScale3D(FVector(1));Lever->SetVisibility(false);}
    SafetyPin->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Characters/Grab/SM_GrenadePin.SM_GrenadePin")));
    if (UMaterialInterface* M=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Characters/Grab/M_Grenade.M_Grenade"))) Housing->SetMaterial(0,M);
}
void ASPGrabGrenade::Tick(float Delta)
{
    Super::Tick(Delta);
    const ASPGameState* GS=GetWorld()->GetGameState<ASPGameState>();
    if (HasAuthority() && GS && GS->VoiceEpoch!=Epoch) {Destroy();return;}
    if (bExploded)
    {UpdateBlast(Delta);return;}
    if (!GS || !ArmedAt) return;
    const float T=GS->GetServerWorldTimeSeconds()-ArmedAt;
    if (HasAuthority() && GS->VoiceEpoch!=Epoch) {Destroy();return;}
    const bool PairValid=IsValid(Captor) && IsValid(Victim) && Captor->IsFinishing()
        && Captor->Grab.Finisher==ESPFinisher::Grenade && Captor->Grab.Partner==Victim;
    if (HasAuthority() && !bThrown && !bPlanted && !PairValid && T<0.f) {Destroy();return;} // Pin was never pulled.
    if (HasAuthority() && !bThrown && !bPlanted && !bDetached && PairValid && T>=.85f)
    {bPlanted=true;ForceNetUpdate();}
    SafetyPin->SetVisibility(!bThrown && !bPlanted && !bDetached && T<.35f && PairValid);
    if (SafetyPin->IsVisible()) SafetyPin->SetWorldLocation(Captor->GetMesh()->GetSocketLocation(TEXT("thumb_03_l")));
    Housing->SetVisibility(!bPlanted);
    if (HasAuthority() && bPlanted && IsValid(Victim) && Victim->Health>0 && !PairValid && Victim->PanicUntil<ArmedAt+FuseSeconds)
    {Victim->PanicStartedAt=GS->GetServerWorldTimeSeconds();Victim->PanicUntil=ArmedAt+FuseSeconds+.2f;Victim->GetCharacterMovement()->StopMovementImmediately();Victim->ForceNetUpdate();Victim->ClientFeedback(TEXT("LIVE GRENADE IN WAISTBAND"));}
    if (!bThrown && bPlanted && IsValid(Victim))
        SetActorLocation(Victim->GetMesh()->GetSocketLocation(TEXT("pelvis"))+Victim->GetActorForwardVector()*10.f-FVector(0,0,8));
    else if (!bThrown && !bDetached)
    {
        if (PairValid) SetActorLocation(SPHandContacts::GrenadeCenter(Captor->GetMesh()));
        else
        {
            bDetached=true;
            if (HasAuthority())
            {FHitResult H;FCollisionQueryParams Q(SCENE_QUERY_STAT(DroppedGrenade),false,this);Q.AddIgnoredActor(Captor);Q.AddIgnoredActor(Victim);
             if (GetWorld()->LineTraceSingleByChannel(H,GetActorLocation(),GetActorLocation()-FVector(0,0,250),ECC_Visibility,Q)) SetActorLocation(H.ImpactPoint+FVector(0,0,5));}
        }
    }
    if (!HasAuthority() || T<FuseSeconds) return;
    bExploded=true;Projectile->StopMovementImmediately();Projectile->Deactivate();Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);ForceNetUpdate();OnRep_Exploded();SetLifeSpan(8.f);
    TArray<TWeakObjectPtr<ASPCharacter>> Targets;
    for (TActorIterator<ASPCharacter> It(GetWorld());It;++It) if (It->Health>0 && FVector::Dist(It->GetActorLocation(),GetActorLocation())<200.f) Targets.Add(*It);
    for (const auto& Weak:Targets) if (ASPCharacter* P=Weak.Get())
    {
        FHitResult H;FCollisionQueryParams Q(SCENE_QUERY_STAT(GrenadeDamage),false,this);Q.AddIgnoredActor(P);if (IsValid(Victim)) Q.AddIgnoredActor(Victim);
        if (GetWorld()->LineTraceSingleByChannel(H,GetActorLocation(),P->GetActorLocation(),ECC_Visibility,Q)) continue;
        const float Distance=FVector::Dist(GetActorLocation(),P->GetActorLocation());FDamageEvent Event;
        P->TakeDamage(Distance<=110.f?100.f:60.f*(200.f-Distance)/90.f,Event,IsValid(Captor)?Captor->GetController():nullptr,this);
    }
}
void ASPGrabGrenade::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(ASPGrabGrenade,bThrown);DOREPLIFETIME(ASPGrabGrenade,bPlanted);DOREPLIFETIME(ASPGrabGrenade,Victim);DOREPLIFETIME(ASPGrabGrenade,Captor);DOREPLIFETIME(ASPGrabGrenade,ArmedAt);DOREPLIFETIME(ASPGrabGrenade,Epoch);DOREPLIFETIME(ASPGrabGrenade,bExploded);
}
