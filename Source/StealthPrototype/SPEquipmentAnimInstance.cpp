#include "SPEquipmentAnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "Animation/AnimNode_SequencePlayer.h"
#include "AnimNodes/AnimNode_SequenceEvaluator.h"
#include "AnimNodes/AnimNode_LayeredBoneBlend.h"
#include "AnimNodes/AnimNode_TwoWayBlend.h"
#include "Animation/AnimSequence.h"
#include "Prototype.h"
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
    }
    virtual FAnimNode_Base* GetCustomRootNode() override {return &ThrowLayer;}
    virtual void PreUpdate(UAnimInstance* Instance,float Delta) override
    {
        FAnimInstanceProxy::PreUpdate(Instance,Delta);
        const USPEquipmentAnimInstance* I=CastChecked<USPEquipmentAnimInstance>(Instance);
        if (Move.GetSequence()!=I->Locomotion)
        {PreviousMove.SetSequence(Move.GetSequence()?Move.GetSequence():I->Locomotion.Get());PreviousMove.SetExplicitTime(Move.GetCurrentAssetTime());MoveFade=Move.GetSequence()?0.f:1.f;Move.SetSequence(I->Locomotion);Move.SetAccumulatedTime(0.f);}
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
    }
};
FAnimInstanceProxy* USPEquipmentAnimInstance::CreateAnimInstanceProxy() {return new FSPEquipmentAnimProxy(this);}
void USPEquipmentAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* Proxy) {delete static_cast<FSPEquipmentAnimProxy*>(Proxy);}
float USPEquipmentAnimInstance::LocomotionTime() const {return GetProxyOnGameThread<FSPEquipmentAnimProxy>().Move.GetCurrentAssetTime();}
