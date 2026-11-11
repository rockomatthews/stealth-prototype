#include "SPEquipmentAnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "Animation/AnimNode_SequencePlayer.h"
#include "AnimNodes/AnimNode_SequenceEvaluator.h"
#include "AnimNodes/AnimNode_LayeredBoneBlend.h"
#include "AnimNodes/AnimNode_TwoWayBlend.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimNodeSpaceConversions.h"
#include "BoneControllers/AnimNode_TwoBoneIK.h"
#include "BoneControllers/AnimNode_ModifyBone.h"
#include "Prototype.h"
#include "SPHandContacts.h"
#include "SPTraversalMovement.h"
#include "Components/SkeletalMeshComponent.h"

struct FSPEquipmentAnimProxy : public FAnimInstanceProxy
{
    FAnimNode_SequencePlayer_Standalone Move;
    FAnimNode_SequenceEvaluator_Standalone PreviousMove;
    FAnimNode_TwoWayBlend MoveBlend;
    float MoveFade=1.f;
    FAnimNode_SequenceEvaluator_Standalone Equip;
    FAnimNode_LayeredBoneBlend Layer;
    FAnimNode_SequenceEvaluator_Standalone Throw;
    FAnimNode_LayeredBoneBlend ThrowLayer;
    FAnimNode_ConvertLocalToComponentSpace GripSpace;
    FAnimNode_ModifyBone AimRight;
    FAnimNode_ModifyBone AimLeft;
    FAnimNode_TwoBoneIK SupportGrip;
    FAnimNode_ConvertComponentToLocalSpace GripResult;
    FSPEquipmentAnimProxy(UAnimInstance* Instance):FAnimInstanceProxy(Instance)
    {
        MoveBlend.A.SetLinkNode(&PreviousMove);MoveBlend.B.SetLinkNode(&Move);MoveBlend.Alpha=1.f;
        Layer.BasePose.SetLinkNode(&MoveBlend);
        Layer.AddPose();Layer.BlendPoses[0].SetLinkNode(&Equip);
        FBranchFilter Left;Left.BoneName=TEXT("clavicle_l");Left.BlendDepth=0;
        FBranchFilter Right;Right.BoneName=TEXT("clavicle_r");Right.BlendDepth=0;
        Layer.LayerSetup[0].BranchFilters={Left,Right};
        Layer.BlendWeights[0]=0.f;
        ThrowLayer.BasePose.SetLinkNode(&Layer);ThrowLayer.AddPose();ThrowLayer.BlendPoses[0].SetLinkNode(&Throw);
        FBranchFilter Torso;Torso.BoneName=TEXT("spine_01");Torso.BlendDepth=0;ThrowLayer.LayerSetup[0].BranchFilters={Torso};ThrowLayer.BlendWeights[0]=0;
        GripSpace.LocalPose.SetLinkNode(&ThrowLayer);AimRight.ComponentPose.SetLinkNode(&GripSpace);AimLeft.ComponentPose.SetLinkNode(&AimRight);SupportGrip.ComponentPose.SetLinkNode(&AimLeft);GripResult.ComponentPose.SetLinkNode(&SupportGrip);
        AimRight.BoneToModify.BoneName=TEXT("clavicle_r");AimLeft.BoneToModify.BoneName=TEXT("clavicle_l");
        for (auto* Aim:{&AimRight,&AimLeft}) {Aim->RotationMode=BMM_Additive;Aim->RotationSpace=BCS_ComponentSpace;Aim->Alpha=0.f;}
        SupportGrip.IKBone.BoneName=TEXT("hand_l");SupportGrip.EffectorLocationSpace=BCS_ComponentSpace;SupportGrip.JointTargetLocationSpace=BCS_ComponentSpace;
        SupportGrip.bAllowStretching=false;SupportGrip.bMaintainEffectorRelRot=true;SupportGrip.Alpha=0.f;
    }
    virtual FAnimNode_Base* GetCustomRootNode() override {return &GripResult;}
    virtual void PreUpdate(UAnimInstance* Instance,float Delta) override
    {
        FAnimInstanceProxy::PreUpdate(Instance,Delta);
        const USPEquipmentAnimInstance* I=CastChecked<USPEquipmentAnimInstance>(Instance);
        if (Move.GetSequence()!=I->Locomotion)
        {PreviousMove.SetSequence(Move.GetSequence()?Move.GetSequence():I->Locomotion.Get());PreviousMove.SetExplicitTime(Move.GetCurrentAssetTime());MoveFade=Move.GetSequence()?0.f:1.f;if (const auto* C=Cast<ASPCharacter>(Instance->GetOwningActor());C && (C->IsFinishing() || C->IsKnockedOut() || C->IsChokeExiting())) MoveFade=1.f;Move.SetSequence(I->Locomotion);Move.SetAccumulatedTime(0.f);}
        MoveFade=FMath::Min(1.f,MoveFade+Delta/.22f);MoveBlend.Alpha=MoveFade;
        Move.SetLoopAnimation(I->bLoopLocomotion);Move.SetPlayRate(I->bExplicitLocomotion?0.f:I->LocomotionRate);
        if (I->bExplicitLocomotion)
        {
            float Sample=I->ExplicitLocomotionTime;
            // Sample the pulling phases from the rendered root, after movement
            // and network smoothing. Clock-only sampling lets corrections slide
            // planted hands/knees ahead of the body at low frame rates.
            if (const ASPCharacter* C=Cast<ASPCharacter>(Instance->GetOwningActor());
                C && I->Locomotion && I->Locomotion->GetFName()==TEXT("SpyVentEntry"))
            {
                const auto& M=C->Traversal()->Motion;
                if (M.bEnteringVent && M.VentPhaseTime>=.5f)
                {
                    const FVector Root=Instance->GetSkelMeshComponent()->GetComponentLocation()+FVector(0,0,42);
                    float Progress=0;
                    if (M.VentPhaseTime<1.65f)
                    {const float Rise=M.VentPhaseTime<1.4f?120.f:30.f;Progress=(Root.Z-(M.Target.Z-Rise))/Rise;}
                    else
                    {const float Distance=M.VentPhaseTime<2.3f?75.f:40.f;const FVector Forward=C->GetActorForwardVector();Progress=FVector::DotProduct(Root-(M.Target-Forward*Distance),Forward)/Distance;}
                    Sample=M.VentPhaseTime+M.Duration*FMath::Clamp(Progress,0.f,1.f);
                }
            }
            Move.SetAccumulatedTime(Sample);
        }
        Equip.SetSequence(I->Equipment?I->Equipment.Get():I->Locomotion.Get());
        Throw.SetSequence(I->Throw?I->Throw.Get():I->Locomotion.Get());Throw.SetExplicitTime(I->ThrowTime);ThrowLayer.BlendWeights[0]=I->Throw?I->ThrowWeight:0.f;
        Equip.SetExplicitTime(I->EquipmentTime);Layer.BlendWeights[0]=I->Equipment?I->EquipmentWeight:0.f;
        SupportGrip.Alpha=0.f;
        AimRight.Alpha=AimLeft.Alpha=0.f;
        if (auto* C=Cast<ASPCharacter>(Instance->GetOwningActor());C && Instance->GetSkelMeshComponent()->GetFName()!=TEXT("FirstPersonArms") && C->WeaponReady() && !C->BlocksGrabCombat() && I->EquipmentWeight>.95f && I->ThrowWeight<.01f)
        {
            const float Pitch=FMath::Clamp((C->IsInspectingAppearance()?0.f:FRotator::NormalizeAxis(C->GetBaseAimRotation().Pitch)),-70.f,70.f);
            AimRight.Rotation=AimLeft.Rotation=FRotator(0,0,Pitch);AimRight.Alpha=AimLeft.Alpha=1.f;
        }
        if (auto* C=Cast<ASPCharacter>(Instance->GetOwningActor());C && C->WeaponReady() && !C->IsPanicking() && (I->EquipmentWeight>.95f || C->IsRestrained()) && (I->ThrowWeight<.01f || (C->IsRestrained() && !C->IsCaptor())))
        {
            auto* Mesh=Instance->GetSkelMeshComponent();const bool View=Mesh->GetFName()==TEXT("FirstPersonArms");
            auto* Gun=Cast<USkeletalMeshComponent>(C->GetDefaultSubobjectByName(View?TEXT("FirstPersonWeapon"):TEXT("EquippedWeapon")));
            if (Gun && (C->IsSpy() || Gun->DoesSocketExist(TEXT("support_grip"))))
            {
                const FTransform Frame=Mesh->GetComponentTransform();
                SupportGrip.EffectorLocation=Frame.InverseTransformPosition((C->IsSpy()?Gun->GetComponentTransform().TransformPosition(SPHandContacts::LauncherPalmLocal):Gun->GetSocketLocation(TEXT("support_grip"))+Gun->GetComponentTransform().TransformVector(SPHandContacts::SupportSocketToPalm))-(Mesh->GetSocketLocation(TEXT("middle_01_l"))-Mesh->GetSocketLocation(TEXT("hand_l")))*.5f);
                SupportGrip.JointTargetLocation=Frame.InverseTransformPosition(Mesh->GetSocketLocation(TEXT("lowerarm_l"))-C->GetActorRightVector()*15.f-FVector(0,0,15));
                SupportGrip.Alpha=1.f;
            }
        }
    }
};
FAnimInstanceProxy* USPEquipmentAnimInstance::CreateAnimInstanceProxy() {return new FSPEquipmentAnimProxy(this);}
void USPEquipmentAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* Proxy) {delete static_cast<FSPEquipmentAnimProxy*>(Proxy);}
float USPEquipmentAnimInstance::LocomotionTime() const {return GetProxyOnGameThread<FSPEquipmentAnimProxy>().Move.GetCurrentAssetTime();}
