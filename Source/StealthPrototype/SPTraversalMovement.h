#pragma once
#include "CoreMinimal.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "SPTraversalMovement.generated.h"

UENUM(BlueprintType)
enum class ESPTraversal : uint8 { Grounded, Vaulting, Hanging, Climbing, Rope, RopeExit };

USTRUCT(BlueprintType)
struct FSPTraversalMotion
{
    GENERATED_BODY()
    UPROPERTY() ESPTraversal State = ESPTraversal::Grounded;
    UPROPERTY() FVector Start = FVector::ZeroVector;
    UPROPERTY() FVector Target = FVector::ZeroVector;
    UPROPERTY() float ServerStart = 0;
    UPROPERTY() float Duration = 0;
    UPROPERTY() uint16 Revision = 0;
    UPROPERTY() bool bVentCrouch=false;
    UPROPERTY() bool bEnteringVent=false;
    UPROPERTY() float VentStartedAt=0;
    UPROPERTY() float VentPhaseTime=0;
    UPROPERTY() float RopeBaseZ=90;
};

UCLASS()
class STEALTHPROTOTYPE_API USPTraversalMovement : public UCharacterMovementComponent
{
    GENERATED_BODY()
public:
    USPTraversalMovement();
    UPROPERTY(ReplicatedUsing=OnRep_Motion, BlueprintReadOnly) FSPTraversalMotion Motion;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Traversal") float Reach = 120.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Traversal") float MaxLedgeHeight = 220.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Traversal") float MinLedgeHeight = 65.f;
    bool TryTraversal();
    bool TryRope();
    virtual bool CanCrouchInCurrentState() const override;
    virtual void UpdateCharacterStateBeforeMovement(float DeltaSeconds) override;
    virtual void ProcessLanded(const FHitResult& Hit,float RemainingTime,int32 Iterations) override;
    virtual void HandleImpact(const FHitResult& Hit,float TimeSlice=0.f,const FVector& MoveDelta=FVector::ZeroVector) override;
    void SetRopeInput(float Axis);
    bool IsOnRope() const {return Motion.State==ESPTraversal::Rope || Motion.State==ESPTraversal::RopeExit;}
    UPROPERTY(EditDefaultsOnly,Category="Traversal") float RopeSpeed=120.f;
    bool Climb();
    void Drop();
    bool IsTraversing() const { return Motion.State != ESPTraversal::Grounded; }
    virtual void TickComponent(float Delta, ELevelTick Tick, FActorComponentTickFunction* Function) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
private:
    UFUNCTION() void OnRep_Motion();
    void StartMotion(ESPTraversal State, const FVector& Target, float Duration);
    bool ClearAt(const FVector& Location) const;
    float ServerTime() const;
    FVector StandOutside, StandInside;
    TWeakObjectPtr<UPrimitiveComponent> Ledge;
    int32 Stage = 0;
    uint16 SourceID = 0;
    TWeakObjectPtr<class ASPRope> ActiveRope;
    float RopeAxis=0;
    float RopeInputAt=-10;
    int32 RopeStage=0;
    void TickRope();
};
