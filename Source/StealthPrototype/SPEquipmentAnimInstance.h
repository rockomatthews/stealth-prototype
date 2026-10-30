#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "SPEquipmentAnimInstance.generated.h"

// Locomotion stays on the legs while authored equipment poses drive the arms.
UCLASS(Transient)
class STEALTHPROTOTYPE_API USPEquipmentAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
public:
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> Locomotion;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> Equipment;
    float LocomotionRate=1.f;
    bool bLoopLocomotion=true;
    float EquipmentWeight=0.f;
    float EquipmentTime=0.f;
    float LocomotionTime() const;
protected:
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
    virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override;
};
