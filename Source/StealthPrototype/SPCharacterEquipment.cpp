#include "Prototype.h"
#include "EngineUtils.h"
#include "Camera/CameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Animation/AnimSequence.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

int32 ASPCharacter::GadgetAmmo() const
{
    return SelectedGadget()==ESPSpyGadget::StickyCamera?GadgetInventory.Cameras:GadgetInventory.TrackingDarts;
}
FString ASPCharacter::GadgetName() const
{
    return SelectedGadget()==ESPSpyGadget::StickyCamera?TEXT("Sticky camera"):TEXT("Spy Bullet");
}
FString ASPCharacter::GadgetHUD(bool bGamepad) const
{
    return FString::Printf(TEXT("GADGET: %s [%d]%s | %s select | Cameras %d / Bullets %d"),
        *GadgetName(),GadgetAmmo(),GadgetAmmo()==0?TEXT(" EMPTY"):TEXT(""),
        bGamepad?TEXT("D-pad Down"):TEXT("R"),GadgetInventory.Cameras,GadgetInventory.TrackingDarts);
}
float ASPCharacter::TrackingSeconds() const
{
    return Health>0 && !IsSpy()?FMath::Max(0.f,TrackedUntil-ServerNow()):0.f;
}
bool ASPCharacter::IsOnSpyRadar() const
{
    if (IsSpy() || !IsRoundActive()) return false;
    if (TrackingSeconds()>0) return true;
    for (TActorIterator<ASPSpyBulletSensor> It(GetWorld());It;++It)
        if (FVector::DistSquared(GetActorLocation(),It->GetActorLocation())<=FMath::Square(It->DetectionRadius)) return true;
    return false;
}
TArray<ASPCharacter*> ASPCharacter::RadarTargets() const
{
    TArray<ASPCharacter*> Targets;
    if (IsSpy() && IsRoundActive()) for (TActorIterator<ASPCharacter> It(GetWorld());It;++It)
        if (It->IsOnSpyRadar()) Targets.Add(*It);
    return Targets;
}
TArray<FString> ASPCharacter::TrackingContacts() const
{
    TArray<FString> Contacts;
    for (const ASPCharacter* Target:RadarTargets())
    {
        const float Distance=FVector::Distance(Target->GetActorLocation(),GetActorLocation())/100.f;
        Contacts.Add(FString::Printf(TEXT("RADAR MERC | %.0f m | %s"),Distance,Target->TrackingSeconds()>0?TEXT("TAGGED"):TEXT("AREA SENSOR")));
    }
    return Contacts;
}
void ASPCharacter::ClearSpyBulletSensors()
{
    if (HasAuthority()) for (TActorIterator<ASPSpyBulletSensor> It(GetWorld());It;++It)
        if (It->GetOwner()==this) It->Destroy();
}
void ASPCharacter::CycleGadget() {if (!bCameraView) ServerCycleGadget();}
void ASPCharacter::ServerCycleGadget_Implementation()
{
    const double Now=GetWorld()->GetTimeSeconds();
    if (!IsSpy() || !IsRoundActive() || IsRestrained() || IsStunned() || Traversal()->IsTraversing() || Now-LastGadgetSelection<.2 || ServerViewedCamera.IsValid()) return;
    LastGadgetSelection=Now;
    GadgetInventory.Selected=SelectedGadget()==ESPSpyGadget::StickyCamera?ESPSpyGadget::TrackingDart:ESPSpyGadget::StickyCamera;
    ForceNetUpdate();ClientFeedback(FString::Printf(TEXT("%s selected | %d remaining"),*GadgetName(),GadgetAmmo()));
}

float ASPCharacter::ServerNow() const
{
    const AGameStateBase* State=GetWorld()->GetGameState();
    return State?State->GetServerWorldTimeSeconds():GetWorld()->GetTimeSeconds();
}
bool ASPCharacter::IsStunned() const {return Health>0 && (StunnedUntil>ServerNow() || IsKnockedOut() || IsGettingUp());}
bool ASPCharacter::WeaponReady() const
{
    return WeaponState.Mode!=ESPWeapon::Hands && ServerNow()-WeaponState.ChangedAt>=EquipDuration && !Traversal()->IsTraversing() && !IsStunned() && Health>0;
}
bool ASPCharacter::HasReticle() const {return WeaponReady() && !bInspectAppearance && !bCameraView;}
void ASPCharacter::SetWeapon(ESPWeapon Mode)
{
    if (!HasAuthority()) return;
    ServerViewedCamera.Reset();
    WeaponState.Mode=Mode;WeaponState.ChangedAt=ServerNow();++WeaponState.Revision;
    bAiming=false;ForceNetUpdate();OnRep_Weapon();
}
void ASPCharacter::OnRep_Weapon() {bAiming=false;ResetCameraView();}
void ASPCharacter::SwitchWeapon() {ServerSwitchWeapon();}
void ASPCharacter::ServerSwitchWeapon_Implementation()
{
    if (!IsRoundActive() || IsThrowingGrenade() || IsRestrained() || IsStunned() || Traversal()->IsTraversing() || ServerNow()-WeaponState.ChangedAt<EquipDuration) return;
    const ESPWeapon Next=IsSpy()?(WeaponState.Mode==ESPWeapon::Hands?ESPWeapon::Taser:ESPWeapon::Hands):
        (WeaponState.Mode==ESPWeapon::Carbine?ESPWeapon::Hands:ESPWeapon::Carbine);
    SetWeapon(Next);
}
void ASPCharacter::ResetCameraView()
{
    if (!bCameraView) return;
    if (APlayerController* PC=Cast<APlayerController>(Controller)) PC->SetViewTargetWithBlend(this,.15f);
    bCameraView=false;bCameraZoomIn=bCameraZoomOut=false;bAiming=false;
    if (IsLocallyControlled() && !GetWorld()->bIsTearingDown) ServerViewCamera(nullptr);
}
void ASPCharacter::ViewStickyCamera()
{
    if (bCameraView) {ResetCameraView();return;}
    if (!IsLocallyControlled() || !IsSpy() || !IsRoundActive() || IsRestrained() || IsStunned() || Traversal()->IsTraversing() || !IsValid(DeployedCamera)) return;
    if (APlayerController* PC=Cast<APlayerController>(Controller)) {ServerInteract(false);ServerViewCamera(DeployedCamera);bAiming=false;bCameraZoomIn=bCameraZoomOut=false;PC->SetViewTargetWithBlend(DeployedCamera,.15f);bCameraView=true;}
}
void ASPCharacter::ServerViewCamera_Implementation(ASPStickyCamera* Viewed)
{
    ServerViewedCamera.Reset();
    if (IsValid(Viewed) && Viewed==DeployedCamera && Viewed->GetOwner()==this && IsSpy() && IsRoundActive() && !IsRestrained() && !IsStunned() && !Traversal()->IsTraversing()) ServerViewedCamera=Viewed;
}
void ASPCharacter::ServerCameraAction_Implementation(ASPStickyCamera* Viewed,bool bGas)
{
    if (!IsValid(Viewed) || Viewed!=DeployedCamera || ServerViewedCamera.Get()!=Viewed || Viewed->GetOwner()!=this || !IsSpy() || !IsRoundActive() || IsRestrained() || IsStunned() || Traversal()->IsTraversing()) return;
    if (bGas) ClientFeedback(Viewed->ReleaseGas()?TEXT("Camera gas released"):TEXT("Camera gas empty"));
    else ClientFeedback(Viewed->Noise()?TEXT("Camera distraction playing"):TEXT("Camera speaker cooling down"));
}
void ASPCharacter::MulticastWeaponFire_Implementation()
{
    Recoil=1.f;
    UAnimSequence* Clip=IsSpy()?LauncherFire:CarbineFire;
    if (Clip) {HeldWeapon->PlayAnimation(Clip,false);FirstPersonWeapon->PlayAnimation(Clip,false);}
}
void ASPCharacter::UpdateEquipment(float Delta)
{
    const bool Alive=Health>0;
    const float Progress=FMath::Clamp((ServerNow()-WeaponState.ChangedAt)/EquipDuration,0.f,1.f);
    const float Target=WeaponState.Mode==ESPWeapon::Hands?1.f-Progress:Progress;
    EquipAlpha=Alive && !IsKnockedOut() && !IsRestrained() && !Traversal()->IsTraversing()?Target:0.f;
    const bool Throwing=IsThrowingGrenade();const float ThrowT=ServerNow()-ThrowStartedAt;
    if (Throwing) EquipAlpha*=ThrowT<.12f?1.f-ThrowT/.12f:FMath::Clamp((ThrowT-.72f)/.246667f,0.f,1.f);
    const bool HoldingGrenade=Throwing && ThrowT>=.125f && ThrowT<.42f;
    WorldThrowGrenade->SetOwnerNoSee(!bInspectAppearance);WorldThrowGrenade->SetVisibility(HoldingGrenade);
    FirstPersonThrowGrenade->SetVisibility(HoldingGrenade && !bInspectAppearance);
    Recoil=FMath::FInterpTo(Recoil,0.f,Delta,18.f);
    const bool Armed=WeaponState.Mode!=ESPWeapon::Hands;
    const bool ThirdPerson=IsSpy() || bInspectAppearance;
    if (!IsSpy() && !bInspectAppearance) {float Height=IsKnockedOut()?0.f:60.f;if (IsGettingUp()) {const float T=FMath::Clamp((ServerNow()-RecoveryShield.GetUpAt)/MercGetUpSeconds,0.f,1.f);Height=FMath::Lerp(-RecoveryShield.CapsuleRise,60.f,T*T*(3.f-2.f*T));}Boom->SetRelativeLocation(FVector(0,0,Height));}
    if (IsSpy() && !bInspectAppearance)
    {const bool Vent=IsInsideVent();Boom->TargetArmLength=FMath::FInterpTo(Boom->TargetArmLength,Vent?95.f:SpyCameraDistance,Delta,8.f);Boom->SetRelativeLocation(FVector(0,0,FMath::FInterpTo(Boom->GetRelativeLocation().Z,Vent?12.f:60.f,Delta,8.f)));}
    bUseControllerRotationYaw=!IsKnockedOut() && (IsCaptor() || !ThirdPerson || (IsSpy() && Armed && !bInspectAppearance));
    GetCharacterMovement()->bOrientRotationToMovement=ThirdPerson && !bUseControllerRotationYaw;

    // Apply the animated head's delta to a hinge authored in mesh reference space.
    const FTransform HeadPose=GetMesh()->GetSocketTransform(TEXT("head"));
    const FTransform Pivot(FQuat::Identity,FVector(0,11,174));
    GoggleHinge->SetWorldTransform(Pivot*HeadReference.Inverse()*HeadPose);
    GoggleAngle=FMath::FInterpTo(GoggleAngle,bNightVision?0.f:-105.f,Delta,10.f);

    // Lenses rotate with the assembly, not the fixed mounting bracket.
    const FQuat Flip(FVector::ForwardVector,FMath::DegreesToRadians(-GoggleAngle));
    GoggleAssembly->SetRelativeRotation(Flip);
    for (int32 I=0;I<2;++I)
    {
        UStaticMeshComponent* Lens=I==0?GoggleLeft:GoggleRight;
        const FVector Down(I==0?-5.6f:5.6f,13.2f,-5.5f);
        Lens->SetRelativeLocation(Flip.RotateVector(Down));
        Lens->SetRelativeRotation((Flip*FRotator(90,0,0).Quaternion()).Rotator());
        Lens->SetVisibility(Alive && IsSpy() && bNightVision && GoggleAngle>-12.f);
    }
    if (LensMaterial) LensMaterial->SetScalarParameterValue(TEXT("Enabled"),Alive && bNightVision?1.f:0.f);
    GoggleAssembly->SetVisibility(Alive && IsSpy());

    USkeletalMesh* Asset=IsSpy()?LauncherAsset.Get():CarbineAsset.Get();
    if (HeldWeapon->GetSkeletalMeshAsset()!=Asset) {HeldWeapon->SetSkeletalMesh(Asset);FirstPersonWeapon->SetSkeletalMesh(Asset);}
    const FTransform Spine=GetMesh()->GetSocketTransform(TEXT("spine_03"));
    const FTransform Back(FRotator(-90,0,0),IsSpy()?FVector(-12,-18,143):FVector(0,-21,128));
    const FTransform Holstered=Back*SpineReference.Inverse()*Spine;
    const FVector Hand=GetMesh()->GetSocketLocation(TEXT("hand_r"));
    FRotator Aim=bInspectAppearance?GetActorRotation():GetBaseAimRotation();Aim.Pitch+=Recoil*2.5f;
    const FTransform InHand(Aim,Hand+Aim.Vector()*(IsSpy()?3.f:1.f));
    FTransform Weapon;Weapon.Blend(Holstered,InHand,EquipAlpha);
    HeldWeapon->SetWorldTransform(Weapon);
    HeldWeapon->SetOwnerNoSee(!ThirdPerson);
    HeldWeapon->SetVisibility(Alive && Asset);
    FirstPersonWeapon->SetVisibility(Alive && !IsSpy() && !bInspectAppearance && Armed && !bCameraView && (!Throwing || EquipAlpha>.1f));
    const float AimBlend=IsAiming()?1.f:0.f;
    const FTransform YawFrame(FRotator(0,GetBaseAimRotation().Yaw,0),Camera->GetComponentLocation());
    const FTransform CameraFrame(GetBaseAimRotation(),Camera->GetComponentLocation());
    FTransform ArmsTransform=GetMesh()->GetComponentTransform().GetRelativeTransform(YawFrame)*CameraFrame;
    const FVector CameraRight=CameraFrame.GetRotation().GetRightVector();
    const FVector CameraUp=CameraFrame.GetRotation().GetUpVector();
    ArmsTransform.AddToTranslation(CameraFrame.GetRotation().RotateVector(FirstPersonViewOffset)+CameraRight*(-12.f*AimBlend)+CameraUp*(8.f*AimBlend-20.f*(1.f-(Throwing?1.f:EquipAlpha))));
    FirstPersonArms->SetWorldTransform(ArmsTransform);
    FirstPersonArms->SetVisibility(FirstPersonWeapon->IsVisible() || (Alive && Throwing && !bInspectAppearance));
    FirstPersonWeapon->SetWorldLocation(FirstPersonArms->GetSocketLocation(TEXT("hand_r"))+Aim.Vector());
    FirstPersonWeapon->SetWorldRotation(Aim);

}
FString ASPCharacter::EquipmentReport() const
{
    TSharedRef<FJsonObject> R=MakeShared<FJsonObject>();
    R->SetNumberField(TEXT("weapon"),static_cast<int32>(WeaponState.Mode));R->SetStringField(TEXT("selectedGadget"),SelectedGadget()==ESPSpyGadget::StickyCamera?TEXT("StickyCamera"):TEXT("TrackingDart"));
    R->SetNumberField(TEXT("gadgetAmmo"),GadgetAmmo());R->SetNumberField(TEXT("cameraAmmo"),GadgetInventory.Cameras);
    R->SetNumberField(TEXT("trackingAmmo"),GadgetInventory.TrackingDarts);R->SetNumberField(TEXT("trackingSeconds"),TrackingSeconds());
    R->SetStringField(TEXT("gadgetHUD"),GadgetHUD(true));
    TArray<TSharedPtr<FJsonValue>> Contacts;
    for (const FString& Contact:TrackingContacts()) Contacts.Add(MakeShared<FJsonValueString>(Contact));
    R->SetArrayField(TEXT("trackingContacts"),Contacts);
    R->SetStringField(TEXT("cameraActor"),GetPathNameSafe(DeployedCamera));R->SetNumberField(TEXT("equipAlpha"),EquipAlpha);
    int32 Sensors=0;
    for (TActorIterator<ASPSpyBulletSensor> It(GetWorld());It;++It) if (It->GetOwner()==this) ++Sensors;
    R->SetNumberField(TEXT("sensorCount"),Sensors);R->SetBoolField(TEXT("onSpyRadar"),IsOnSpyRadar());
    R->SetBoolField(TEXT("throwAsset"),MercThrow!=nullptr);R->SetBoolField(TEXT("worldGrenadeProp"),WorldThrowGrenade->IsVisible());R->SetBoolField(TEXT("firstPersonGrenadeProp"),FirstPersonThrowGrenade->IsVisible());
    R->SetNumberField(TEXT("worldGrenadeGrip"),FVector::Dist(WorldThrowGrenade->GetComponentLocation(),GetMesh()->GetSocketLocation(TEXT("hand_r"))));
    R->SetNumberField(TEXT("firstPersonGrenadeGrip"),FVector::Dist(FirstPersonThrowGrenade->GetComponentLocation(),FirstPersonArms->GetSocketLocation(TEXT("hand_r"))));
    R->SetBoolField(TEXT("weaponReady"),WeaponReady());R->SetBoolField(TEXT("reticle"),HasReticle());
    R->SetBoolField(TEXT("stunned"),IsStunned());R->SetBoolField(TEXT("cameraView"),bCameraView);
    R->SetBoolField(TEXT("cameraDeployed"),IsValid(DeployedCamera));
    R->SetBoolField(TEXT("serverViewingCamera"),ServerViewedCamera.IsValid());
    if (IsValid(DeployedCamera))
    {
        R->SetNumberField(TEXT("stickyYaw"),DeployedCamera->LookYaw);R->SetNumberField(TEXT("stickyPitch"),DeployedCamera->LookPitch);
        R->SetNumberField(TEXT("stickyFOV"),DeployedCamera->Camera->FieldOfView);
        R->SetBoolField(TEXT("stickyNV"),DeployedCamera->bNightVision);R->SetBoolField(TEXT("gasAvailable"),DeployedCamera->GasAvailable());
        R->SetBoolField(TEXT("gasVisible"),DeployedCamera->GasCloud->IsVisible());R->SetBoolField(TEXT("cameraAudioReady"),DeployedCamera->AudioReady());
        R->SetNumberField(TEXT("noiseCues"),DeployedCamera->NoiseCues);R->SetNumberField(TEXT("gasCues"),DeployedCamera->GasCues);
        R->SetNumberField(TEXT("lastNoiseAt"),DeployedCamera->LastNoiseAt);R->SetNumberField(TEXT("gasReleasedAt"),DeployedCamera->GasReleasedAt);
    }
    R->SetStringField(TEXT("weaponMesh"),GetPathNameSafe(HeldWeapon->GetSkeletalMeshAsset()));
    R->SetStringField(TEXT("weaponParent"),HeldWeapon->GetAttachParent()?HeldWeapon->GetAttachParent()->GetName():TEXT("None"));
    R->SetBoolField(TEXT("gogglesIndependent"),GoggleAssembly->GetStaticMesh()!=nullptr);
    if (const UStaticMesh* Optics=GoggleAssembly->GetStaticMesh())
        R->SetNumberField(TEXT("goggleCenterHeight"),GoggleAssembly->GetRelativeTransform().TransformPosition(Optics->GetBounds().Origin).Z);
    R->SetBoolField(TEXT("goggleLights"),GoggleLeft->IsVisible() && GoggleRight->IsVisible());
    R->SetBoolField(TEXT("firstPersonWeapon"),FirstPersonWeapon->IsVisible());
    R->SetBoolField(TEXT("firstPersonArms"),FirstPersonArms->IsVisible() && FirstPersonArms->GetSkeletalMeshAsset()!=nullptr);
    R->SetNumberField(TEXT("gripDistance"),FVector::Dist(FirstPersonWeapon->GetComponentLocation(),FirstPersonArms->GetSocketLocation(TEXT("hand_r"))));
    FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);FJsonSerializer::Serialize(R,Writer);return Text;
}
