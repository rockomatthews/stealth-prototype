#include "SPEquipmentAnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "Animation/AnimNode_SequencePlayer.h"
#include "AnimNodes/AnimNode_SequenceEvaluator.h"
#include "AnimNodes/AnimNode_LayeredBoneBlend.h"
#include "Animation/AnimSequence.h"

struct FSPEquipmentAnimProxy : public FAnimInstanceProxy
{
    FAnimNode_SequencePlayer_Standalone Move;
    FAnimNode_SequenceEvaluator_Standalone Equip;
    FAnimNode_LayeredBoneBlend Layer;
    FSPEquipmentAnimProxy(UAnimInstance* Instance):FAnimInstanceProxy(Instance)
    {
        Layer.BasePose.SetLinkNode(&Move);
        Layer.AddPose();Layer.BlendPoses[0].SetLinkNode(&Equip);
        FBranchFilter Left;Left.BoneName=TEXT("clavicle_l");Left.BlendDepth=0;
        FBranchFilter Right;Right.BoneName=TEXT("clavicle_r");Right.BlendDepth=0;
        Layer.LayerSetup[0].BranchFilters={Left,Right};
        Layer.BlendWeights[0]=0.f;
    }
    virtual FAnimNode_Base* GetCustomRootNode() override {return &Layer;}
    virtual void PreUpdate(UAnimInstance* Instance,float Delta) override
    {
        FAnimInstanceProxy::PreUpdate(Instance,Delta);
        const USPEquipmentAnimInstance* I=CastChecked<USPEquipmentAnimInstance>(Instance);
        if (Move.GetSequence()!=I->Locomotion) {Move.SetSequence(I->Locomotion);Move.SetAccumulatedTime(0.f);}
        Move.SetLoopAnimation(I->bLoopLocomotion);Move.SetPlayRate(I->LocomotionRate);
        Equip.SetSequence(I->Equipment?I->Equipment.Get():I->Locomotion.Get());
        Equip.SetExplicitTime(I->EquipmentTime);Layer.BlendWeights[0]=I->Equipment?I->EquipmentWeight:0.f;
    }
};
FAnimInstanceProxy* USPEquipmentAnimInstance::CreateAnimInstanceProxy() {return new FSPEquipmentAnimProxy(this);}
void USPEquipmentAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* Proxy) {delete static_cast<FSPEquipmentAnimProxy*>(Proxy);}
float USPEquipmentAnimInstance::LocomotionTime() const {return GetProxyOnGameThread<FSPEquipmentAnimProxy>().Move.GetCurrentAssetTime();}
