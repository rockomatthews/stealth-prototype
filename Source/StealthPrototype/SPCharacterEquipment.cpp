#include "Prototype.h"
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

float ASPCharacter::ServerNow() const
{
    const AGameStateBase* State=GetWorld()->GetGameState();
    return State?State->GetServerWorldTimeSeconds():GetWorld()->GetTimeSeconds();
}
bool ASPCharacter::IsStunned() const {return Health>0 && StunnedUntil>ServerNow();}
bool ASPCharacter::WeaponReady() const
{
    return WeaponState.Mode!=ESPWeapon::Hands && ServerNow()-WeaponState.ChangedAt>=EquipDuration && !Traversal()->IsTraversing() && !IsStunned() && Health>0;
}
bool ASPCharacter::HasReticle() const {return WeaponReady() && !bInspectAppearance && !bCameraView;}
void ASPCharacter::SetWeapon(ESPWeapon Mode)
{
    if (!HasAuthority()) return;
    WeaponState.Mode=Mode;WeaponState.ChangedAt=ServerNow();++WeaponState.Revision;
    bAiming=false;ForceNetUpdate();OnRep_Weapon();
}
void ASPCharacter::OnRep_Weapon() {bAiming=false;ResetCameraView();}
void ASPCharacter::SwitchWeapon() {ServerSwitchWeapon();}
void ASPCharacter::ServerSwitchWeapon_Implementation()
{
    if (!IsRoundActive() || IsStunned() || Traversal()->IsTraversing() || ServerNow()-WeaponState.ChangedAt<EquipDuration) return;
    const ESPWeapon Next=IsSpy()?(WeaponState.Mode==ESPWeapon::Hands?ESPWeapon::Taser:ESPWeapon::Hands):
        (WeaponState.Mode==ESPWeapon::Carbine?ESPWeapon::Hands:ESPWeapon::Carbine);
    SetWeapon(Next);
}
void ASPCharacter::ResetCameraView()
{
    if (!bCameraView) return;
    if (APlayerController* PC=Cast<APlayerController>(Controller)) PC->SetViewTargetWithBlend(this,.15f);
    bCameraView=false;
}
void ASPCharacter::ViewStickyCamera()
{
    if (bCameraView) {ResetCameraView();return;}
    if (!IsLocallyControlled() || !IsSpy() || !IsRoundActive() || IsStunned() || Traversal()->IsTraversing() || !DeployedCamera) return;
    if (APlayerController* PC=Cast<APlayerController>(Controller)) {PC->SetViewTargetWithBlend(DeployedCamera,.15f);bCameraView=true;}
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
    EquipAlpha=Alive && !Traversal()->IsTraversing()?Target:0.f;
    Recoil=FMath::FInterpTo(Recoil,0.f,Delta,18.f);
    const bool Armed=WeaponState.Mode!=ESPWeapon::Hands;
    const bool ThirdPerson=IsSpy() || bInspectAppearance;
    bUseControllerRotationYaw=!ThirdPerson || (IsSpy() && Armed && !bInspectAppearance);
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
    FirstPersonWeapon->SetVisibility(Alive && !IsSpy() && !bInspectAppearance && Armed && !bCameraView);
    const float AimBlend=IsAiming()?1.f:0.f;
    const FTransform YawFrame(FRotator(0,GetBaseAimRotation().Yaw,0),Camera->GetComponentLocation());
    const FTransform CameraFrame(GetBaseAimRotation(),Camera->GetComponentLocation());
    FTransform ArmsTransform=GetMesh()->GetComponentTransform().GetRelativeTransform(YawFrame)*CameraFrame;
    const FVector CameraRight=CameraFrame.GetRotation().GetRightVector();
    const FVector CameraUp=CameraFrame.GetRotation().GetUpVector();
    ArmsTransform.AddToTranslation(CameraRight*(-12.f*AimBlend)+CameraUp*(8.f*AimBlend-20.f*(1.f-EquipAlpha)));
    FirstPersonArms->SetWorldTransform(ArmsTransform);
    FirstPersonArms->SetVisibility(FirstPersonWeapon->IsVisible());
    FirstPersonWeapon->SetWorldLocation(FirstPersonArms->GetSocketLocation(TEXT("hand_r"))+Aim.Vector());
    FirstPersonWeapon->SetWorldRotation(Aim);

}
FString ASPCharacter::EquipmentReport() const
{
    TSharedRef<FJsonObject> R=MakeShared<FJsonObject>();
    R->SetNumberField(TEXT("weapon"),static_cast<int32>(WeaponState.Mode));R->SetStringField(TEXT("selectedGadget"),TEXT("StickyCamera"));R->SetNumberField(TEXT("equipAlpha"),EquipAlpha);
    R->SetBoolField(TEXT("weaponReady"),WeaponReady());R->SetBoolField(TEXT("reticle"),HasReticle());
    R->SetBoolField(TEXT("stunned"),IsStunned());R->SetBoolField(TEXT("cameraView"),bCameraView);
    R->SetBoolField(TEXT("cameraDeployed"),IsValid(DeployedCamera));
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
