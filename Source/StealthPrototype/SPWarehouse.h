#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SPWarehouse.generated.h"
class USceneComponent;
class UStaticMeshComponent;
class UActorComponent;
UCLASS()
class STEALTHPROTOTYPE_API ASPWarehouse : public AActor
{
    GENERATED_BODY()
public:
    ASPWarehouse();
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;
    void Build();
    UFUNCTION(CallInEditor,BlueprintCallable) void RebuildWarehouse();
    UPROPERTY(Transient) TArray<TObjectPtr<UActorComponent>> Generated;
};
UCLASS()
class STEALTHPROTOTYPE_API ASPVentRoute : public AActor
{
    GENERATED_BODY()
public:
    ASPVentRoute();
    UPROPERTY(Replicated) FVector HalfSize=FVector(84,1400,60);
    bool Contains(const FVector& Point) const;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
UCLASS()
class STEALTHPROTOTYPE_API ASPRope : public AActor
{
    GENERATED_BODY()
public:
    ASPRope();
    UPROPERTY(Replicated) FVector Entry=FVector::ZeroVector;
    UPROPERTY(Replicated) float FloorHeight=780.f;
    FVector Bottom() const;
    FVector Top() const;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
UCLASS()
class STEALTHPROTOTYPE_API ASPMercDoor : public AActor
{
    GENERATED_BODY()
public:
    ASPMercDoor();
    virtual void Tick(float Delta) override;
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Leaf;
    UPROPERTY(Replicated) bool bOpen=false;
    float Alpha=0;
};
