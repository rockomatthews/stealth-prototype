#pragma once
#include "CoreMinimal.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "SPRecoveryFX.generated.h"

class UMaterialInstanceDynamic;

UCLASS()
class STEALTHPROTOTYPE_API USPRecoveryFX : public UInstancedStaticMeshComponent
{
    GENERATED_BODY()
public:
    USPRecoveryFX();
    virtual void BeginPlay() override;
    virtual void TickComponent(float Delta,ELevelTick Tick,FActorComponentTickFunction* Function) override;
    float Glow=0;
private:
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> ArcMaterial;
};
