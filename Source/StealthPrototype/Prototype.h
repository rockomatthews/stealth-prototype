#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/HUD.h"
#include "SPTraversalMovement.h"
#include "GameFramework/PlayerController.h"
#include "Prototype.generated.h"

class UCameraComponent;
class USpringArmComponent;
class USpotLightComponent;
class USceneComponent;
class UStaticMeshComponent;
class UInputAction;
class UInputMappingContext;
class UAnimSequence;
class USoundBase;
struct FInputActionValue;

UENUM(BlueprintType)
enum class ESPTeam : uint8 { Spy, Merc };
UENUM(BlueprintType)
enum class ESPPhase : uint8 { Waiting, Playing, SpiesWin, MercsWin };

UCLASS()
class STEALTHPROTOTYPE_API ASPPlayerState : public APlayerState
{
    GENERATED_BODY()
public:
    UPROPERTY(Replicated, BlueprintReadOnly) ESPTeam Team = ESPTeam::Spy;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};

UCLASS()
class STEALTHPROTOTYPE_API ASPGameState : public AGameStateBase
{
    GENERATED_BODY()
public:
    UPROPERTY(Replicated, BlueprintReadOnly) bool bPractice = false;
    UPROPERTY(Replicated, BlueprintReadOnly) ESPPhase Phase = ESPPhase::Waiting;
    UPROPERTY(Replicated, BlueprintReadOnly) float RoundSeconds = 180.f;
    UPROPERTY(Replicated, BlueprintReadOnly) float HackProgress = 0.f;
    UPROPERTY(Replicated, BlueprintReadOnly) int32 Spies = 0;
    UPROPERTY(Replicated, BlueprintReadOnly) int32 Mercs = 0;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};

UCLASS()
class STEALTHPROTOTYPE_API ASPCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    ASPCharacter(const FObjectInitializer& ObjectInitializer);
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual float TakeDamage(float Amount, const FDamageEvent& Event,
        AController* InstigatorController, AActor* Causer) override;
    bool IsSpy() const;
    bool IsRoundActive() const;
    void ConfigureRole();
    bool WantsToHack() const { return bInteractHeld && Health > 0.f && !Traversal()->IsTraversing(); }
    USPTraversalMovement* Traversal() const { return CastChecked<USPTraversalMovement>(GetCharacterMovement()); }
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Role") float SpySpeed = 350.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Role") float MercSpeed = 280.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Role") float SpyCameraDistance = 280.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Combat") float ShotDamage = 34.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Combat") float TakedownReach = 180.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Interaction") float HackReach = 200.f;
    UFUNCTION(BlueprintCallable) void PracticeRole();
    UFUNCTION(Server, Reliable, BlueprintCallable) void ServerTraversal();
    UFUNCTION(Server, Reliable, BlueprintCallable) void ServerDrop();
    UFUNCTION(Client, Reliable) void ClientFeedback(const FString& Text);
    void Exercise(const FString& Action);
    FString Feedback;
    float FeedbackUntil = 0;
    bool NightVisionEnabled() const { return bNightVision; }
    UPROPERTY(Replicated, BlueprintReadOnly) float Health = 100.f;
protected:
    UPROPERTY(VisibleAnywhere) USpringArmComponent* Boom;
    UPROPERTY(VisibleAnywhere) UCameraComponent* Camera;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Body;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Head;
    UPROPERTY(VisibleAnywhere) USpotLightComponent* Flashlight;
    UPROPERTY(Transient) UInputMappingContext* Mapping;
    UPROPERTY(Transient) TArray<TObjectPtr<UInputAction>> Actions;
    UPROPERTY(Transient) TArray<TObjectPtr<UAnimSequence>> Clips;
    UPROPERTY(Transient) USoundBase* StepSound;
    UPROPERTY(Transient) USoundBase* ShotSound;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Mask;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Vest;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Gun;
    UPROPERTY(VisibleAnywhere) USceneComponent* GoggleHinge;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* GoggleLeft;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* GoggleRight;
    UFUNCTION(Server,Reliable) void ServerNightVision(bool Enabled);
    UPROPERTY(ReplicatedUsing=OnRep_Flashlight) bool bFlashlight = false;
    UFUNCTION() void OnRep_Flashlight();
    UFUNCTION(Server, Reliable) void ServerInteract(bool bHeld);
    UFUNCTION(Server, Reliable) void ServerAttack();
    UFUNCTION(Server, Reliable) void ServerFlashlight();
    void Move(const FInputActionValue& Value);
    void Look(const FInputActionValue& Value);
    void NightVision();
    void UpdateAnimation(float Delta);
    UFUNCTION(NetMulticast, Unreliable) void MulticastSound(USoundBase* Sound, FVector Location);
    UPROPERTY(Replicated) bool bNightVision = false;
    float StepClock = 0;
    float LandingClock = 0;
    bool bWasFalling = false;
    int32 PlayingClip = INDEX_NONE;
    void JumpPressed();
    void CrouchPressed();
    void InteractPressed();
    void InteractReleased();
    void AttackPressed();
    bool bInteractHeld = false;
    bool bRoleConfigured = false;
    double LastAttackTime = -10.0;
};

// Primitive geometry is intentional: concept renders are not rigged meshes.
UCLASS()
class STEALTHPROTOTYPE_API ASPArena : public AActor
{
    GENERATED_BODY()
public:
    ASPArena();
};

UCLASS()
class STEALTHPROTOTYPE_API ASPTerminal : public AActor
{
    GENERATED_BODY()
public:
    ASPTerminal();
};

UCLASS()
class STEALTHPROTOTYPE_API ASPPlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    UFUNCTION(Client,Reliable) void ClientExercise(const FString& Action);
    UFUNCTION(Exec) void Practice();
    UFUNCTION(Exec) void Match();
};

UCLASS()
class STEALTHPROTOTYPE_API ASPGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ASPGameMode();
    virtual void InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage) override;
    virtual void InitGameState() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void PreLogin(const FString& Options, const FString& Address,
        const FUniqueNetIdRepl& UniqueId, FString& ErrorMessage) override;
    virtual void PostLogin(APlayerController* NewPlayer) override;
    virtual void Logout(AController* Exiting) override;
    virtual AActor* ChoosePlayerStart_Implementation(AController* Player) override;
    void Respawn(AController* Player);
private:
    UPROPERTY() ASPTerminal* Terminal;
    float ResultSeconds = 0.f;
    bool bPracticeRequested = false;
    void RefreshRoster(AController* Exclude = nullptr);
    void ResetRound(AController* Exclude = nullptr);
};

UCLASS()
class STEALTHPROTOTYPE_API ASPHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
};
