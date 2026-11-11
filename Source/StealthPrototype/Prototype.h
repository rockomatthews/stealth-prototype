#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/HUD.h"
#include "SPTraversalMovement.h"
#include "SPVoiceComponent.h"
#include "GameFramework/PlayerController.h"
#include "Prototype.generated.h"

class UBoxComponent;
class USphereComponent;
class UProjectileMovementComponent;
class UCameraComponent;
class USpringArmComponent;
class USpotLightComponent;
class USceneComponent;
class UStaticMeshComponent;
class UInputAction;
class UInputMappingContext;
class UAnimSequence;
class USoundBase;
class USkeletalMeshComponent;
class UMaterialInstanceDynamic;
class ASPStickyCamera;
struct FInputActionValue;

UENUM(BlueprintType)
enum class ESPTeam : uint8 { Spy, Merc };
UENUM(BlueprintType)
enum class ESPPhase : uint8 { Waiting, Playing, SpiesWin, MercsWin };

UENUM(BlueprintType)
enum class ESPWeapon : uint8 { Hands=0, Taser=1, Carbine=3 };

UENUM(BlueprintType)
enum class ESPSpyGadget : uint8 { StickyCamera, TrackingDart };

USTRUCT(BlueprintType)
struct FSPGadgetInventory
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) ESPSpyGadget Selected=ESPSpyGadget::StickyCamera;
    UPROPERTY(BlueprintReadOnly) int32 Cameras=3;
    UPROPERTY(BlueprintReadOnly) int32 TrackingDarts=4;
};

USTRUCT()
struct FSPWeaponState
{
    GENERATED_BODY()
    UPROPERTY() ESPWeapon Mode=ESPWeapon::Hands;
    UPROPERTY() float ChangedAt=-10.f;
    UPROPERTY() uint16 Revision=0;
};

UENUM()
enum class ESPFinisher : uint8 { None, NeckSnap, BackChoke, Grenade };

USTRUCT()
struct FSPGrabState
{
    GENERATED_BODY()
    UPROPERTY() TObjectPtr<class ASPCharacter> Partner;
    UPROPERTY() bool bCaptor=false;
    UPROPERTY() uint32 Token=0;
    UPROPERTY() float StartedAt=0;
    UPROPERTY() ESPFinisher Finisher=ESPFinisher::None;
    UPROPERTY() float FinishStartedAt=0;
};

USTRUCT()
struct FSPKnockout
{
    GENERATED_BODY()
    UPROPERTY() bool bActive=false;
    UPROPERTY() bool bForwardCollapse=false;
    UPROPERTY() float Until=0;
    UPROPERTY() float StartedAt=0;
    UPROPERTY() FVector StandLocation=FVector::ZeroVector;
    UPROPERTY() FVector MeshLocation=FVector(0,0,-88);
    UPROPERTY() float HalfHeight=88;
};

USTRUCT()
struct FSPRecoveryShield
{
    GENERATED_BODY()
    UPROPERTY() float StartedAt=0;
    UPROPERTY() float Until=0;
    UPROPERTY() float GetUpAt=0;
    UPROPERTY() float CapsuleRise=54;
    UPROPERTY() bool bForwardCollapse=false;
};

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
    UPROPERTY(Replicated) uint32 VoiceEpoch=1;
    uint32 NextGrabToken=1;
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
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void UnPossessed() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual float TakeDamage(float Amount, const FDamageEvent& Event,
        AController* InstigatorController, AActor* Causer) override;
    bool IsSpy() const;
    UPROPERTY(ReplicatedUsing=OnRep_Knockout) FSPKnockout Knockout;
    UPROPERTY(Replicated) FSPRecoveryShield RecoveryShield;
    UPROPERTY(EditDefaultsOnly,Category="Combat") float RecoveryShieldSeconds=3.f;
    UPROPERTY(EditDefaultsOnly,Category="Combat") float MercGetUpSeconds=.8f;
    UPROPERTY(VisibleAnywhere) class USPRecoveryFX* RecoveryFX;
    bool HasRecoveryShield() const;
    bool IsGettingUp() const;
    void RepelRecoverySpy(ASPCharacter* Spy);
    UFUNCTION(NetMulticast,Reliable) void MulticastRecoveryRepel(FVector Impulse);
    float LastRecoveryRepel=-10;
    uint32 RecoveryGrabBlocks=0,RecoveryDropBlocks=0,RecoveryShotsFired=0;
    bool IsKnockedOut() const {return Knockout.bActive && Health>0;}
    void UpdateDropAttack();
    bool TryDropKnockoutImpact(const FHitResult& Hit,float FallingSpeed);
    void BeginDropKnockout(ASPCharacter* Spy,bool ForwardCollapse=false);
    void ClearKnockout();
    UFUNCTION() void OnRep_Knockout(FSPKnockout Previous);
    UPROPERTY(EditDefaultsOnly,Category="Combat") float DropKnockoutSeconds=6.f;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> MercKnockout;
    UPROPERTY(EditAnywhere,Category="Camera") FVector FirstPersonViewOffset=FVector(54,0,-8);
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> MercEquipView;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> MercThrowView;
    UPROPERTY(VisibleAnywhere) UBoxComponent* KnockoutHitBox;
    float LastDropAttack=-10;
    uint32 DropKnockoutCount=0;
    ESPWeapon BeforeKnockoutWeapon=ESPWeapon::Hands;
    UPROPERTY(ReplicatedUsing=OnRep_Grab) FSPGrabState Grab;
    bool IsRestrained() const { return Grab.Token!=0; }
    bool IsCaptor() const { return IsRestrained() && Grab.bCaptor; }
    bool IsChokeVictim() const { return IsRestrained() && !Grab.bCaptor && Grab.Finisher==ESPFinisher::BackChoke; }
    bool BlocksGrabInput() const { return IsRestrained() && !IsChokeVictim() && (!IsCaptor() || IsFinishing()); }
    bool BlocksGrabCombat() const { return IsRestrained() && !IsChokeVictim(); }
    double LastShotTime() const {return LastAttackTime;}
    bool TryBeginGrab();
    void EndGrab();
    void ValidateGrab();
    bool IsFinishing() const { return IsRestrained() && Grab.Finisher!=ESPFinisher::None; }
    void UpdateGrab(float Delta);
    void BeginFinisher(bool Extended);
    UFUNCTION(Server,Reliable) void ServerFinishInput(bool Pressed);
    UPROPERTY(EditDefaultsOnly,Category="Grab") float GrabMoveSpeed=85.f;
    UPROPERTY(EditDefaultsOnly,Category="Grab") float FinishHoldSeconds=.5f;
    UPROPERTY(EditDefaultsOnly,Category="Gadgets") int32 StartingMercGrenades=2;
    UPROPERTY(Replicated,BlueprintReadOnly) int32 MercGrenades=2;
    UPROPERTY(EditDefaultsOnly,Category="Gadgets",meta=(ClampMin="100",ClampMax="2000")) float GrenadeThrowSpeed=1050.f;
    UPROPERTY(EditDefaultsOnly,Category="Gadgets",meta=(ClampMin="0.2",ClampMax="5")) float GrenadeThrowCooldown=1.f;
    float LastGrenadeThrowAt=-10.f;
    void ThrowMercGrenade();
    void ReleaseMercGrenade();
    void UpdateGrenadeThrow();
    bool IsThrowingGrenade() const {return !IsSpy() && Health>0 && !BlocksGrabCombat() && !IsStunned() && ServerNow()>=ThrowStartedAt && ServerNow()-ThrowStartedAt<.966667f;}
    UPROPERTY(Replicated) float ThrowStartedAt=-10.f;
    UPROPERTY(Replicated) float PanicStartedAt=-10.f;
    UPROPERTY(Replicated) float PanicUntil=-10.f;
    bool IsPanicking() const {return !IsSpy() && Health>0 && IsRoundActive() && ServerNow()<PanicUntil;}
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> MercPanic;
    bool bThrowPending=false;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> MercThrow;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SpyRopeClip;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SpyVentEntry;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SpyVentCrawl;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SpyVentIdle;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* WorldThrowGrenade;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* FirstPersonThrowGrenade;
    bool IsInsideVent() const;
    UFUNCTION(Server,Unreliable) void ServerRopeInput(float Axis);
    float LastRopeInputSent=-10.f;
    FVector HeardNoisePosition=FVector::ZeroVector;
    float LastHeardNoise=-10;
    float ReticleGap() const {return (IsAiming()?7.f:14.f)+GetVelocity().Size2D()*.018f+Recoil*3.f;}
    FVector SafeGrabPosition=FVector::ZeroVector;
    FRotator SafeGrabFacing=FRotator::ZeroRotator;
    FVector FinishOrigin=FVector::ZeroVector;
    float FinishPressedAt=-1.f;
    bool bFinishSpentGrenade=false;
    float HeldPoseClock=0.f;
    FVector HeldTarget=FVector::ZeroVector;
    FRotator HeldFacing=FRotator::ZeroRotator;
    uint32 HeldPoseToken=0;
    UPROPERTY(Transient) TArray<TObjectPtr<UAnimSequence>> GrabClips;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SpyChokeExit;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> MercChokeFall;
    UPROPERTY(Replicated) float ChokeExitAt=-10.f;
    UPROPERTY(Replicated) float ChokeDeathAt=-10.f;
    bool IsChokeCorpse() const {return !IsSpy() && Health<=0 && ChokeDeathAt>0;}
    UPROPERTY(EditDefaultsOnly,Category="Equipment",meta=(ClampMin="0.5",ClampMax="1.0")) float MercRifleScale=.75f;
    bool IsChokeExiting() const {return IsSpy() && Health>0 && ServerNow()>=ChokeExitAt && ServerNow()<ChokeExitAt+1.6f;}
    TWeakObjectPtr<ASPCharacter> ChokeExitPartner;
    UFUNCTION() void OnRep_Grab(FSPGrabState Previous);
    UFUNCTION(Server,Reliable) void ServerReleaseGrab();
    UFUNCTION(Server,Reliable) void ServerFinishGrab();
    void ToggleVoiceMute();
    ESPWeapon WeaponBeforeGrab=ESPWeapon::Hands;
    bool IsRoundActive() const;
    void ConfigureRole();
    bool WantsToHack() const { return bInteractHeld && Health > 0.f && !IsRestrained() && !Traversal()->IsTraversing(); }
    USPTraversalMovement* Traversal() const { return CastChecked<USPTraversalMovement>(GetCharacterMovement()); }
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Role") float SpySpeed = 350.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Role") float MercSpeed = 280.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Role") float SpyCameraDistance = 280.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Combat") float ShotDamage = 34.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Combat") float TakedownReach = 180.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Interaction") float HackReach = 200.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Controller", meta=(ClampMin="0",ClampMax="0.5")) float StickDeadZone = .18f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Controller") float ControllerYawRate = 150.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Controller") float ControllerPitchRate = 110.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Controller") bool bInvertControllerY = false;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Controller") float AimSensitivity = .45f;
    bool IsAiming() const { return bAiming && WeaponReady() && Health>0; }
    ESPWeapon WeaponMode() const { return WeaponState.Mode; }
    bool WeaponReady() const;
    bool HasReticle() const;
    bool IsStunned() const;
    float ServerNow() const;
    float EquipmentAlpha() const { return EquipAlpha; }
    FString EquipmentReport() const;
    UFUNCTION(BlueprintCallable) void SwitchWeapon();
    UFUNCTION(BlueprintCallable) void ViewStickyCamera();
    UFUNCTION(BlueprintCallable) void CycleGadget();
    ESPSpyGadget SelectedGadget() const { return GadgetInventory.Selected; }
    int32 GadgetAmmo() const;
    FString GadgetName() const;
    FString GadgetHUD(bool bGamepad) const;
    float TrackingSeconds() const;
    TArray<FString> TrackingContacts() const;
    TArray<ASPCharacter*> RadarTargets() const;
    bool IsOnSpyRadar() const;
    void ClearSpyBulletSensors();
    UPROPERTY(EditDefaultsOnly, Category="Gadgets", meta=(ClampMin="0",ClampMax="20")) int32 StartingCameras=3;
    UPROPERTY(EditDefaultsOnly, Category="Gadgets", meta=(ClampMin="0",ClampMax="20")) int32 StartingTrackingDarts=4;
    UPROPERTY(EditDefaultsOnly, Category="Gadgets", meta=(ClampMin="1",ClampMax="30")) float TrackingDuration=12.f;
    UPROPERTY(Replicated) float TrackedUntil=0.f;
    UPROPERTY(EditDefaultsOnly, Category="Equipment") float EquipDuration=.7f;
    UPROPERTY(EditDefaultsOnly, Category="Equipment") float TaserRange=1200.f;
    UPROPERTY(EditDefaultsOnly, Category="Equipment") float StunDuration=3.f;
    UPROPERTY(Replicated) float StunnedUntil=0.f;
    UPROPERTY(Replicated) TObjectPtr<ASPStickyCamera> DeployedCamera;
    // Gadget selection is independent of drawing/holstering the shocker.
    UPROPERTY(Replicated, BlueprintReadOnly) FSPGadgetInventory GadgetInventory;
    bool FlashlightEnabled() const { return bFlashlight; }
    float GogglePitch() const;
    float CameraDistance() const;
    float CameraFOV() const;
    float ActualCameraOffset() const;
    bool IsInspectingAppearance() const { return bInspectAppearance; }
    UFUNCTION(BlueprintCallable) void InspectAppearance();
    TArray<FString> InputKeys() const;
    UFUNCTION(BlueprintCallable) void PracticeRole();
    UFUNCTION(BlueprintCallable) void ChoosePracticeRole(ESPTeam SelectedTeam);
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
    UPROPERTY(VisibleAnywhere) USpotLightComponent* InspectionLight;
    UPROPERTY(Transient) UInputMappingContext* Mapping;
    UPROPERTY(Transient) TArray<TObjectPtr<UInputAction>> Actions;
    UPROPERTY(Transient) TArray<TObjectPtr<UAnimSequence>> Clips;
    UPROPERTY(Transient) TObjectPtr<USkeletalMesh> SpyAppearance;
    UPROPERTY(Transient) TObjectPtr<USkeletalMesh> MercAppearance;
    UPROPERTY(Transient) USoundBase* StepSound;
    UPROPERTY(Transient) USoundBase* ShotSound;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Mask;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Vest;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Gun;
    UPROPERTY(VisibleAnywhere) USkeletalMeshComponent* HeldWeapon;
    UPROPERTY(VisibleAnywhere) USkeletalMeshComponent* FirstPersonWeapon;
    UPROPERTY(VisibleAnywhere) USkeletalMeshComponent* FirstPersonArms;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* GoggleAssembly;
    UPROPERTY(VisibleAnywhere) USceneComponent* GoggleHinge;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* GoggleLeft;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* GoggleRight;
    UPROPERTY(ReplicatedUsing=OnRep_Weapon) FSPWeaponState WeaponState;
    UFUNCTION() void OnRep_Weapon();
    UFUNCTION(Server,Reliable) void ServerSwitchWeapon();
    UFUNCTION(NetMulticast,Unreliable) void MulticastWeaponFire();
    void SetWeapon(ESPWeapon Mode);
    void UpdateEquipment(float Delta);
    void ResetCameraView();
    UPROPERTY(Transient) TObjectPtr<USkeletalMesh> CarbineAsset;
    UPROPERTY(Transient) TObjectPtr<USkeletalMesh> LauncherAsset;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> CarbineFire;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> LauncherFire;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SpyEquip;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> MercEquip;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> LensMaterial;
    float EquipAlpha=0.f;
    float Recoil=0.f;
    bool bCameraView=false;
    bool bCameraZoomIn=false;
    bool bCameraZoomOut=false;
    TWeakObjectPtr<ASPStickyCamera> ServerViewedCamera;
    UFUNCTION(Server,Reliable) void ServerViewCamera(ASPStickyCamera* Viewed);
    UFUNCTION(Server,Reliable) void ServerCameraAction(ASPStickyCamera* Viewed,bool bGas);
    void AttackReleased();
    FTransform HeadReference;
    FTransform SpineReference;
    UFUNCTION(Server,Reliable) void ServerNightVision(bool Enabled);
    UPROPERTY(ReplicatedUsing=OnRep_Flashlight) bool bFlashlight = false;
    UFUNCTION() void OnRep_Flashlight();
    UFUNCTION(Server, Reliable) void ServerInteract(bool bHeld);
    UFUNCTION(Server, Reliable) void ServerAttack();
    UFUNCTION(Server, Reliable) void ServerUseGadget();
    UFUNCTION(Server, Reliable) void ServerCycleGadget();
    double LastGadgetSelection=-10.;
    void FireEquippedWeapon(bool bGadgetShot);
    void GadgetPressed();
    UFUNCTION(Server, Reliable) void ServerFlashlight();
    void Move(const FInputActionValue& Value);
    void Look(const FInputActionValue& Value);
    void LookGamepad(const FInputActionValue& Value);
    void EquipmentPressed();
    void AimPressed();
    void AimReleased();
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
    bool bConfiguredSpy = false;
    bool bUsesMeshyAppearance = false;
    bool bInspectAppearance = false;
    bool bAiming = false;
    float GoggleAngle = -105.f;
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
    ASPPlayerController();
    UPROPERTY(VisibleAnywhere) USPVoiceComponent* Voice;
    UFUNCTION(Server,Unreliable) void ServerVoiceFrame(ESPVoiceChannel Channel,uint32 Epoch,uint32 Token,uint32 Stream,uint32 Sequence,const TArray<uint8>& Data);
    UFUNCTION(Client,Unreliable) void ClientVoiceFrame(int32 Sender,ESPVoiceChannel Channel,uint32 Epoch,uint32 Token,uint32 Stream,uint32 Sequence,const TArray<uint8>& Data);
    UFUNCTION(Client,Reliable) void ClientAirPose(FVector Position,FRotator Facing,float FallingSpeed);
    UFUNCTION(Client,Reliable) void ClientGrabPose(FVector Position,FRotator Facing);
    UFUNCTION(Client,Unreliable) void ClientHeldPose(FVector Position,FRotator Facing,uint32 Token);
    UFUNCTION(Client,Reliable) void ClientVoicePair(int32 Peer,uint32 Token);
    UFUNCTION(Client,Reliable) void ClientVoiceEpoch(uint32 Epoch);
    bool IsAutomationInput() const;
    virtual bool InputKey(const FInputKeyEventArgs& Params) override;
    bool UsingGamepad() const { return bUsingGamepad; }
    UFUNCTION(Client,Reliable) void ClientExercise(const FString& Action);
    UFUNCTION(Exec) void Practice();
    UFUNCTION(Exec) void Match();
    UFUNCTION(Exec) void PracticeSpy();
    UFUNCTION(Exec) void PracticeMerc();
private:
    bool bUsingGamepad = false;
#if WITH_EDITOR
    bool bAutomatedInput = false;
#endif
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
    float LastDrawTime = -1.f;
    virtual void DrawHUD() override;
};

UCLASS()
class STEALTHPROTOTYPE_API ASPStickyCamera : public AActor
{
    GENERATED_BODY()
public:
    ASPStickyCamera();
    UPROPERTY(VisibleAnywhere) UCameraComponent* Camera;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Housing;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* GasCloud;
    virtual void BeginPlay() override;
    virtual void Tick(float Delta) override;
    void Look(float Yaw,float Pitch);
    void Zoom(float Direction,float Delta);
    void ToggleNightVision();
    bool Noise();
    bool ReleaseGas();
    bool GasAvailable() const { return GasReleasedAt<0; }
    float Now() const;
    UPROPERTY(Replicated) float GasReleasedAt=-1.f;
    UPROPERTY(Replicated) float LastNoiseAt=-10.f;
    UPROPERTY(EditDefaultsOnly,Category="Camera") float GasRadius=300.f;
    UPROPERTY(EditDefaultsOnly,Category="Camera") float GasStunDuration=5.f;
    float LookYaw=0.f;
    float LookPitch=0.f;
    bool bNightVision=false;
    int32 NoiseCues=0;
    int32 GasCues=0;
    bool AudioReady() const { return NoiseSound && GasSound; }
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
protected:
    UPROPERTY(Transient) USoundBase* NoiseSound;
    UPROPERTY(Transient) USoundBase* GasSound;
    UPROPERTY(Transient) UMaterialInstanceDynamic* GasMaterial;
    UFUNCTION(NetMulticast,Reliable) void MulticastCue(bool bGas);
};

// Spy Bullets attached to the environment become proximity radar sensors.
UCLASS()
class STEALTHPROTOTYPE_API ASPSpyBulletSensor : public AActor
{
    GENERATED_BODY()
public:
    ASPSpyBulletSensor();
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Housing;
    UPROPERTY(EditDefaultsOnly, Category="Sensor") float DetectionRadius=1000.f;
};

// Shared explosive for thrown merc grenades and spy theft; the fuse survives interruption.
UCLASS()
class STEALTHPROTOTYPE_API ASPGrabGrenade : public AActor
{
    GENERATED_BODY()
public:
    ASPGrabGrenade();
    UPROPERTY(VisibleAnywhere) USphereComponent* Collision;
    UPROPERTY(VisibleAnywhere) UProjectileMovementComponent* Projectile;
    // Shared fuse for thrown and stolen grenades, measured from pin pull.
    UPROPERTY(EditDefaultsOnly,Category="Grenade") float FuseSeconds=2.9f;
    UPROPERTY(Replicated) bool bPlanted=false;
    UPROPERTY(Replicated) bool bThrown=false;
    void Launch(const FVector& Velocity);
    int32 BounceCount=0;
    UFUNCTION() void OnBounce(const FHitResult& Impact,const FVector& Velocity);
    virtual void Tick(float Delta) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Housing;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Lever;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* SafetyPin;
    virtual void BeginPlay() override;
    UPROPERTY(Replicated) TObjectPtr<ASPCharacter> Victim;
    UPROPERTY(Replicated) TObjectPtr<ASPCharacter> Captor;
    UPROPERTY(Replicated) float ArmedAt=0;
    UPROPERTY(Replicated) uint32 Epoch=0;
    UPROPERTY(ReplicatedUsing=OnRep_Exploded) bool bExploded=false;
    UFUNCTION() void OnRep_Exploded();
    bool bDetached=false;
    float BlastStartedAt=-1.f;
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> BlastClouds;
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> BlastFire;
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> BlastBlood;
    TArray<FVector> BloodVelocity;
    TArray<bool> BloodDeposited;
    UPROPERTY(Transient) TObjectPtr<class UPointLightComponent> BlastLight;
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMesh>> FragmentAssets;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> CloudAsset;
    UPROPERTY(Transient) TObjectPtr<class UMaterialInterface> DustMaterial;
    UPROPERTY(Transient) TObjectPtr<class UMaterialInterface> CutMaterial;
    int32 BodyFragmentCount=0;
    void UpdateBlast(float Delta);
};
