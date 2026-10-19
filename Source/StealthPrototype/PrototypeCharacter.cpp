#include "Prototype.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Engine/DamageEvents.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "GameFramework/SpringArmComponent.h"
#include "Animation/AnimSequence.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Net/UnrealNetwork.h"
#include "Sound/SoundBase.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

ASPCharacter::ASPCharacter(const FObjectInitializer& Init)
    : Super(Init.SetDefaultSubobjectClass<USPTraversalMovement>(ACharacter::CharacterMovementComponentName))
{
    PrimaryActorTick.bCanEverTick=true;bReplicates=true;
    GetCapsuleComponent()->InitCapsuleSize(34,88);
    GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility,ECR_Block);
    GetCharacterMovement()->GetNavAgentPropertiesRef().bCanCrouch=true;
    GetCharacterMovement()->SetCrouchedHalfHeight(42.f);
    GetCharacterMovement()->MaxWalkSpeedCrouched=110;
    GetCharacterMovement()->JumpZVelocity=450;
    GetCharacterMovement()->RotationRate=FRotator(0,540,0);
    Boom=CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));Boom->SetupAttachment(RootComponent);
    Boom->SetRelativeLocation(FVector(0,0,60));Boom->bUsePawnControlRotation=true;
    Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));Camera->SetupAttachment(Boom);
    Camera->FieldOfView=85;
    Body=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FallbackBody"));Body->SetupAttachment(RootComponent);
    Body->SetRelativeScale3D(FVector(.55,.4,1.25));Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Head=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FallbackHead"));Head->SetupAttachment(RootComponent);
    Head->SetRelativeLocation(FVector(0,0,68));Head->SetRelativeScale3D(FVector(.35));Head->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    Body->SetStaticMesh(Cylinder.Object);Head->SetStaticMesh(Sphere.Object);
    GetMesh()->SetRelativeLocation(FVector(0,0,-88));GetMesh()->SetRelativeRotation(FRotator(0,-90,0));
    GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> Mannequin(TEXT("/Game/Prototype/Mannequin/SK_Prototype.SK_Prototype"));
    if (Mannequin.Succeeded()) GetMesh()->SetSkeletalMesh(Mannequin.Object);
    Mask=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FabricMask"));Mask->SetupAttachment(GetMesh(),TEXT("head"));
    Mask->SetStaticMesh(Sphere.Object);Mask->SetRelativeScale3D(FVector(.24,.22,.28));Mask->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Vest=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlateCarrier"));Vest->SetupAttachment(GetMesh(),TEXT("spine_03"));
    Vest->SetStaticMesh(Cube.Object);Vest->SetRelativeScale3D(FVector(.38,.24,.42));Vest->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Gun=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WeaponProxy"));Gun->SetupAttachment(Camera);
    Gun->SetStaticMesh(Cube.Object);Gun->SetRelativeLocation(FVector(45,18,-18));Gun->SetRelativeScale3D(FVector(.55,.055,.09));
    Gun->SetCollisionEnabled(ECollisionEnabled::NoCollision);Gun->SetOnlyOwnerSee(true);
    GoggleHinge=CreateDefaultSubobject<USceneComponent>(TEXT("FlipUpGoggleMount"));GoggleHinge->SetupAttachment(GetMesh(),TEXT("head"));
    GoggleHinge->SetRelativeLocation(FVector(10,0,8));
    GoggleLeft=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("LeftNVGOptic"));GoggleLeft->SetupAttachment(GoggleHinge);
    GoggleRight=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RightNVGOptic"));GoggleRight->SetupAttachment(GoggleHinge);
    GoggleLeft->SetStaticMesh(Cylinder.Object);GoggleRight->SetStaticMesh(Cylinder.Object);
    GoggleLeft->SetRelativeLocation(FVector(0,-4,-4));GoggleRight->SetRelativeLocation(FVector(0,4,-4));
    for (auto* Optic:{GoggleLeft,GoggleRight})
    {Optic->SetRelativeScale3D(FVector(.065,.065,.14));Optic->SetRelativeRotation(FRotator(90,0,0));Optic->SetCollisionEnabled(ECollisionEnabled::NoCollision);}
    Flashlight=CreateDefaultSubobject<USpotLightComponent>(TEXT("Flashlight"));Flashlight->SetupAttachment(RootComponent);
    Flashlight->SetRelativeLocation(FVector(20,0,50));Flashlight->Intensity=25000;
    Flashlight->AttenuationRadius=1800;Flashlight->OuterConeAngle=30;Flashlight->SetVisibility(false);
}
void ASPCharacter::BeginPlay()
{
    Super::BeginPlay();
    if (USkeletalMesh* Mesh=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Prototype/Mannequin/SK_Prototype.SK_Prototype"))) GetMesh()->SetSkeletalMesh(Mesh);
    const TCHAR* Names[]={TEXT("Idle"),TEXT("Walk"),TEXT("CrouchIdle"),TEXT("Crouch"),TEXT("Jump"),TEXT("Fall"),TEXT("Land"),TEXT("Vault")};
    for (const TCHAR* Name:Names)
        Clips.Add(LoadObject<UAnimSequence>(nullptr,*FString::Printf(TEXT("/Game/Prototype/Mannequin/%s.%s"),Name,Name)));
    StepSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/Prototype/Audio/Step.Step"));
    ShotSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/Prototype/Audio/Shot.Shot"));
    ConfigureRole();
}
bool ASPCharacter::IsSpy() const
{
    const ASPPlayerState* PS=GetPlayerState<ASPPlayerState>();return PS && PS->Team==ESPTeam::Spy;
}
bool ASPCharacter::IsRoundActive() const
{
    const ASPGameState* GS=GetWorld()->GetGameState<ASPGameState>();
    return GS && (GS->bPractice || GS->Phase==ESPPhase::Playing) && Health>0;
}
void ASPCharacter::ConfigureRole()
{
    if (!GetPlayerState<ASPPlayerState>()) return;
    const bool Spy=IsSpy();Boom->TargetArmLength=Spy?SpyCameraDistance:0;
    Boom->SocketOffset=Spy?FVector(0,40,0):FVector::ZeroVector;
    bUseControllerRotationYaw=!Spy;GetCharacterMovement()->bOrientRotationToMovement=Spy;
    GetCharacterMovement()->MaxWalkSpeed=Spy?SpySpeed:MercSpeed;
    // A 1.05 m passage fits only the spy's crouched capsule.
    GetCharacterMovement()->SetCrouchedHalfHeight(Spy?42.f:60.f);
    GetMesh()->SetOwnerNoSee(!Spy);Body->SetOwnerNoSee(!Spy);Head->SetOwnerNoSee(!Spy);
    Mask->SetOwnerNoSee(!Spy);Vest->SetOwnerNoSee(!Spy);
    if (UMaterialInterface* M=LoadObject<UMaterialInterface>(nullptr,Spy?TEXT("/Game/Prototype/M_Spy.M_Spy"):TEXT("/Game/Prototype/M_Merc.M_Merc")))
    {
        for (int32 I=0;I<GetMesh()->GetNumMaterials();++I) GetMesh()->SetMaterial(I,M);
        Body->SetMaterial(0,M);Head->SetMaterial(0,M);
    }
    if (UMaterialInterface* M=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Prototype/M_Gear.M_Gear")))
    { Mask->SetMaterial(0,M);Vest->SetMaterial(0,M);Gun->SetMaterial(0,M); }
    GoggleLeft->SetOwnerNoSee(!Spy);GoggleRight->SetOwnerNoSee(!Spy);
    bRoleConfigured=true;
}
void ASPCharacter::Tick(float Delta)
{
    Super::Tick(Delta);
    if (!bRoleConfigured || (IsSpy() && Boom->TargetArmLength==0) || (!IsSpy() && Boom->TargetArmLength>0)) ConfigureRole();
    const bool HasMesh=GetMesh()->GetSkeletalMeshAsset()!=nullptr;
    Body->SetVisibility(Health>0 && !HasMesh);Head->SetVisibility(Health>0 && !HasMesh);
    GetMesh()->SetVisibility(Health>0);Mask->SetVisibility(Health>0 && HasMesh);Vest->SetVisibility(Health>0 && HasMesh && !IsSpy());
    Gun->SetVisibility(Health>0 && !IsSpy());
    GoggleLeft->SetVisibility(Health>0 && HasMesh && IsSpy());GoggleRight->SetVisibility(Health>0 && HasMesh && IsSpy());
    GoggleHinge->SetRelativeRotation(FMath::RInterpTo(GoggleHinge->GetRelativeRotation(),FRotator(bNightVision?0.f:-105.f,0,0),Delta,10.f));
    Flashlight->SetWorldRotation(GetBaseAimRotation());Flashlight->SetVisibility(bFlashlight && !IsSpy() && Health>0);
    if ((!IsSpy() || Health<=0) && bNightVision) { NightVision(); }
    if (IsLocallyControlled())
    {
        Camera->PostProcessSettings.bOverride_ColorGain=true;
        Camera->PostProcessSettings.ColorGain=bNightVision?FVector4(.8f,2.8f,.8f,1.f):FVector4(1,1,1,1);
        Camera->PostProcessSettings.bOverride_AutoExposureBias=true;
        Camera->PostProcessSettings.AutoExposureBias=bNightVision?3.f:0.f;
    }
    UpdateAnimation(Delta);
    if (HasAuthority() && IsRoundActive() && GetVelocity().Size2D()>35 && GetCharacterMovement()->IsMovingOnGround())
    {
        StepClock+=Delta;
        if (StepClock>(bIsCrouched?.65f:.42f)) {StepClock=0;MulticastSound(StepSound,GetActorLocation());}
    }
}
void ASPCharacter::UpdateAnimation(float Delta)
{
    if (!GetMesh()->GetSkeletalMeshAsset() || Clips.Num()<8) return;
    const bool Falling=GetCharacterMovement()->IsFalling();
    if (bWasFalling && !Falling) LandingClock=.22f;
    bWasFalling=Falling;LandingClock=FMath::Max(0.f,LandingClock-Delta);
    int32 Index=GetVelocity().Size2D()>15?(bIsCrouched?3:1):(bIsCrouched?2:0);
    bool Loop=true;
    if (Falling) Index=GetVelocity().Z>50?4:5;
    else if (LandingClock>0) {Index=6;Loop=false;}
    else if (Traversal()->Motion.State==ESPTraversal::Vaulting || Traversal()->Motion.State==ESPTraversal::Climbing) {Index=7;Loop=false;}
    if (Clips[Index] && Index!=PlayingClip) {GetMesh()->PlayAnimation(Clips[Index],Loop);PlayingClip=Index;}
    if (Index==1 || Index==3) GetMesh()->SetPlayRate(FMath::Clamp(GetVelocity().Size2D()/(Index==1?200.f:110.f),.5f,1.8f));
    else GetMesh()->SetPlayRate(1.f);
}
void ASPCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    UEnhancedInputComponent* EI=CastChecked<UEnhancedInputComponent>(Input);
    Mapping=NewObject<UInputMappingContext>(this);
    auto Action=[this](EInputActionValueType Type)
    {
        UInputAction* A=NewObject<UInputAction>(this);A->ValueType=Type;Actions.Add(A);return A;
    };
    UInputAction* MoveAction=Action(EInputActionValueType::Axis2D);
    auto Axis=[this,MoveAction](FKey Key,bool Y,bool Negative)
    {
        FEnhancedActionKeyMapping& K=Mapping->MapKey(MoveAction,Key);
        if (Negative) K.Modifiers.Add(NewObject<UInputModifierNegate>(this));
        if (Y) {auto* S=NewObject<UInputModifierSwizzleAxis>(this);S->Order=EInputAxisSwizzle::YXZ;K.Modifiers.Add(S);}
    };
    Axis(EKeys::W,true,false);Axis(EKeys::S,true,true);Axis(EKeys::D,false,false);Axis(EKeys::A,false,true);
    EI->BindAction(MoveAction,ETriggerEvent::Triggered,this,&ASPCharacter::Move);
    UInputAction* LookAction=Action(EInputActionValueType::Axis2D);
    Mapping->MapKey(LookAction,EKeys::MouseX);
    auto& MouseY=Mapping->MapKey(LookAction,EKeys::MouseY);
    MouseY.Modifiers.Add(NewObject<UInputModifierNegate>(this));
    auto* Swizzle=NewObject<UInputModifierSwizzleAxis>(this);Swizzle->Order=EInputAxisSwizzle::YXZ;MouseY.Modifiers.Add(Swizzle);
    EI->BindAction(LookAction,ETriggerEvent::Triggered,this,&ASPCharacter::Look);
    auto Button=[&](FKey Key,auto Function)
    {UInputAction* A=Action(EInputActionValueType::Boolean);Mapping->MapKey(A,Key);EI->BindAction(A,ETriggerEvent::Started,this,Function);return A;};
    UInputAction* JumpAction=Button(EKeys::SpaceBar,&ASPCharacter::JumpPressed);
    EI->BindAction(JumpAction,ETriggerEvent::Completed,this,&ACharacter::StopJumping);
    Button(EKeys::LeftControl,&ASPCharacter::CrouchPressed);
    UInputAction* HackAction=Button(EKeys::E,&ASPCharacter::InteractPressed);
    EI->BindAction(HackAction,ETriggerEvent::Completed,this,&ASPCharacter::InteractReleased);
    EI->BindAction(HackAction,ETriggerEvent::Canceled,this,&ASPCharacter::InteractReleased);
    Button(EKeys::LeftMouseButton,&ASPCharacter::AttackPressed);Button(EKeys::F,&ASPCharacter::ServerFlashlight);
    Button(EKeys::N,&ASPCharacter::NightVision);Button(EKeys::Tab,&ASPCharacter::PracticeRole);
    if (APlayerController* PC=Cast<APlayerController>(Controller))
        if (UEnhancedInputLocalPlayerSubsystem* Sub=ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
        {Sub->ClearAllMappings();Sub->AddMappingContext(Mapping,0);}
}
void ASPCharacter::Move(const FInputActionValue& Value)
{
    if (!IsRoundActive() || !Controller || Traversal()->IsTraversing()) return;
    FVector2D V=Value.Get<FVector2D>();FRotator R(0,Controller->GetControlRotation().Yaw,0);
    AddMovementInput(R.Vector(),V.Y);AddMovementInput(FRotationMatrix(R).GetUnitAxis(EAxis::Y),V.X);
}
void ASPCharacter::Look(const FInputActionValue& Value)
{const FVector2D V=Value.Get<FVector2D>();AddControllerYawInput(V.X);AddControllerPitchInput(V.Y);}
void ASPCharacter::JumpPressed() { if (IsRoundActive() && IsSpy()) ServerTraversal(); }
void ASPCharacter::ServerTraversal_Implementation()
{
    if (!IsRoundActive() || !IsSpy()) return;
    if (Traversal()->Motion.State==ESPTraversal::Hanging) {Traversal()->Climb();return;}
    if (!Traversal()->TryTraversal() && !Traversal()->IsTraversing()) Jump();
}
void ASPCharacter::ServerDrop_Implementation() { if (IsRoundActive() && Traversal()->IsTraversing()) Traversal()->Drop(); }
void ASPCharacter::CrouchPressed()
{
    if (!IsRoundActive()) return;
    if (Traversal()->IsTraversing()) {ServerDrop();return;}
    if (bIsCrouched) UnCrouch();else Crouch();
}
void ASPCharacter::PracticeRole()
{
#if !UE_BUILD_SHIPPING
    ASPGameState* GS=GetWorld()->GetGameState<ASPGameState>();
    if (HasAuthority() && GS && GS->bPractice)
    {
        Traversal()->Drop();UnCrouch();
        if (ASPPlayerState* PS=GetPlayerState<ASPPlayerState>()) {PS->Team=IsSpy()?ESPTeam::Merc:ESPTeam::Spy;PS->ForceNetUpdate();}
        bNightVision=false;ConfigureRole();ClientFeedback(IsSpy()?TEXT("Practice: spy"):TEXT("Practice: merc"));
    }
#endif
}
void ASPCharacter::NightVision()
{
    if (bNightVision) {bNightVision=false;ServerNightVision(false);}
    else if (IsSpy() && IsRoundActive()) {bNightVision=true;ServerNightVision(true);}
}
void ASPCharacter::ServerNightVision_Implementation(bool Enabled) {bNightVision=Enabled && IsSpy() && IsRoundActive();ForceNetUpdate();}
void ASPCharacter::InteractPressed() {ServerInteract(true);}
void ASPCharacter::InteractReleased() {ServerInteract(false);}
void ASPCharacter::AttackPressed() {ServerAttack();}
void ASPCharacter::ServerInteract_Implementation(bool Held) {bInteractHeld=Held && IsSpy() && IsRoundActive() && !Traversal()->IsTraversing();}
void ASPCharacter::ServerFlashlight_Implementation() {if (IsRoundActive() && !IsSpy()) {bFlashlight=!bFlashlight;OnRep_Flashlight();}}
void ASPCharacter::OnRep_Flashlight() {Flashlight->SetVisibility(bFlashlight && Health>0);}
void ASPCharacter::ClientFeedback_Implementation(const FString& Text) {Feedback=Text;FeedbackUntil=GetWorld()->GetTimeSeconds()+2.f;}
void ASPCharacter::MulticastSound_Implementation(USoundBase* Sound,FVector Location)
{
    if (!Sound || GetNetMode()==NM_DedicatedServer) return;
    FSoundAttenuationSettings Settings;Settings.bAttenuate=true;Settings.AttenuationShape=EAttenuationShape::Sphere;
    Settings.AttenuationShapeExtents=FVector(100);Settings.FalloffDistance=Sound==StepSound?(bIsCrouched?400:1000):2500;
    USoundAttenuation* Att=NewObject<USoundAttenuation>(this);Att->Attenuation=Settings;
    UGameplayStatics::PlaySoundAtLocation(this,Sound,Location,FRotator::ZeroRotator,1.f,1.f,0.f,Att);
}
void ASPCharacter::ServerAttack_Implementation()
{
    if (!IsRoundActive() || !Controller || Traversal()->IsTraversing()) return;
    const double Now=GetWorld()->GetTimeSeconds();if (Now-LastAttackTime<(IsSpy()?.8:.22)) return;LastAttackTime=Now;
    FVector Eye;FRotator Aim;GetActorEyesViewPoint(Eye,Aim);
    if (!IsSpy()) MulticastSound(ShotSound,Eye);
    FCollisionQueryParams Q(SCENE_QUERY_STAT(Weapon),false,this);FHitResult Hit;
    GetWorld()->LineTraceSingleByChannel(Hit,Eye,Eye+Aim.Vector()*(IsSpy()?TakedownReach:5000),ECC_Visibility,Q);
    ASPCharacter* Victim=Cast<ASPCharacter>(Hit.GetActor());
    if (!Victim || Victim->Health<=0 || Victim->IsSpy()==IsSpy()) {ClientFeedback(TEXT("No hit"));return;}
    if (IsSpy() && FVector::DotProduct(Victim->GetActorForwardVector(),(GetActorLocation()-Victim->GetActorLocation()).GetSafeNormal2D())>-.45f)
    {ClientFeedback(TEXT("Takedown requires rear approach"));return;}
    FDamageEvent Event;Victim->TakeDamage(IsSpy()?100:ShotDamage,Event,Controller,this);
    ClientFeedback(Victim->Health<=0?TEXT("Target down"):TEXT("Hit"));
}
float ASPCharacter::TakeDamage(float Amount,const FDamageEvent& Event,AController* InstigatorController,AActor* Causer)
{
    if (!HasAuthority() || !IsRoundActive() || Amount<=0) return 0;
    const float Applied=FMath::Min(Health,Amount);Health-=Applied;ForceNetUpdate();ClientFeedback(TEXT("Taking damage"));
    if (Health<=0)
    {
        bInteractHeld=false;bFlashlight=false;bNightVision=false;Traversal()->Drop();GetCharacterMovement()->StopMovementImmediately();GetCharacterMovement()->DisableMovement();
        const TWeakObjectPtr<AController> PC(Controller);FTimerHandle Handle;
        GetWorldTimerManager().SetTimer(Handle,FTimerDelegate::CreateWeakLambda(this,[this,PC]()
        {if (PC.IsValid()) if (ASPGameMode* GM=GetWorld()->GetAuthGameMode<ASPGameMode>()) GM->Respawn(PC.Get());}),5,false);
    }
    return Applied;
}
void ASPCharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(ASPCharacter,Health);DOREPLIFETIME(ASPCharacter,bFlashlight);DOREPLIFETIME(ASPCharacter,bNightVision);
}

void ASPCharacter::Exercise(const FString& Action)
{
#if WITH_EDITOR
    if (Action==TEXT("traverse")) ServerTraversal();
    else if (Action==TEXT("drop")) ServerDrop();
    else if (Action==TEXT("hack")) ServerInteract(true);
    else if (Action==TEXT("release")) ServerInteract(false);
    else if (Action==TEXT("fire")) ServerAttack();
    else if (Action==TEXT("role")) PracticeRole();
    else if (Action==TEXT("crouch")) CrouchPressed();
    else if (Action==TEXT("nightvision")) NightVision();
#endif
}
