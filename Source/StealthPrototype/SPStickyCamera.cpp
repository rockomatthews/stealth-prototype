#include "Prototype.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/AudioComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Sound/SoundAttenuation.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

ASPStickyCamera::ASPStickyCamera()
{
    bReplicates=true;SetReplicateMovement(true);PrimaryActorTick.bCanEverTick=true;
    Housing=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CameraHousing"));SetRootComponent(Housing);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    Housing->SetStaticMesh(Sphere.Object);Housing->SetRelativeScale3D(FVector(.09f,.09f,.05f));
    Housing->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("StickyCameraView"));Camera->SetupAttachment(Housing);
    Camera->SetAbsolute(false,false,true);Camera->FieldOfView=85.f;
    GasCloud=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("GasCloud"));GasCloud->SetupAttachment(Housing);
    GasCloud->SetStaticMesh(Sphere.Object);GasCloud->SetAbsolute(false,false,true);
    GasCloud->SetCollisionEnabled(ECollisionEnabled::NoCollision);GasCloud->SetCastShadow(false);GasCloud->SetVisibility(false);
    InitialLifeSpan=60.f;
}
void ASPStickyCamera::BeginPlay()
{
    Super::BeginPlay();
    NoiseSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/Prototype/Audio/CameraLure.CameraLure"));
    GasSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/Prototype/Audio/CameraGas.CameraGas"));
    if (UMaterialInterface* Material=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Prototype/M_CameraGas.M_CameraGas")))
    {GasMaterial=UMaterialInstanceDynamic::Create(Material,this);GasCloud->SetMaterial(0,GasMaterial);}
}
float ASPStickyCamera::Now() const
{
    const AGameStateBase* GS=GetWorld()->GetGameState();
    return GS?GS->GetServerWorldTimeSeconds():GetWorld()->GetTimeSeconds();
}
void ASPStickyCamera::Tick(float Delta)
{
    Super::Tick(Delta);
    const float Age=Now()-GasReleasedAt;
    const bool Visible=GasReleasedAt>=0 && Age>=0 && Age<2.5f && GasMaterial;
    GasCloud->SetVisibility(Visible);
    if (Visible)
    {
        GasCloud->SetWorldScale3D(FVector(GasRadius/50.f*FMath::Clamp(Age/.3f,.05f,1.f)));
        GasMaterial->SetScalarParameterValue(TEXT("Density"),.16f*(1.f-Age/2.5f));
    }
}
void ASPStickyCamera::Look(float Yaw,float Pitch)
{
    LookYaw=FMath::Clamp(LookYaw+Yaw,-85.f,85.f);LookPitch=FMath::Clamp(LookPitch+Pitch,-60.f,60.f);
    Camera->SetRelativeRotation(FRotator(LookPitch,LookYaw,0));
}
void ASPStickyCamera::Zoom(float Direction,float Delta)
{Camera->SetFieldOfView(FMath::Clamp(Camera->FieldOfView+Direction*Delta*45.f,30.f,85.f));}
void ASPStickyCamera::ToggleNightVision()
{
    bNightVision=!bNightVision;
    Camera->PostProcessSettings.bOverride_ColorGain=true;
    Camera->PostProcessSettings.ColorGain=bNightVision?FVector4(.8f,2.8f,.8f,1):FVector4(1,1,1,1);
    Camera->PostProcessSettings.bOverride_AutoExposureBias=true;
    Camera->PostProcessSettings.AutoExposureBias=bNightVision?3.f:0.f;
}
bool ASPStickyCamera::Noise()
{
    if (!HasAuthority() || Now()-LastNoiseAt<2.f) return false;
    LastNoiseAt=Now();ForceNetUpdate();MulticastCue(false);return true;
}
bool ASPStickyCamera::ReleaseGas()
{
    if (!HasAuthority() || !GasAvailable()) return false;
    GasReleasedAt=Now();ForceNetUpdate();MulticastCue(true);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(CameraGas),false,this);
    for (TActorIterator<ASPCharacter> It(GetWorld());It;++It) Query.AddIgnoredActor(*It);
    for (TActorIterator<ASPCharacter> It(GetWorld());It;++It)
    {
        if (It->IsSpy() || !It->IsRoundActive() || FVector::DistSquared(GetActorLocation(),It->GetActorLocation())>FMath::Square(GasRadius)) continue;
        FHitResult Hit;
        if (GetWorld()->LineTraceSingleByChannel(Hit,GetActorLocation(),It->GetActorLocation(),ECC_Visibility,Query)) continue;
        It->StunnedUntil=FMath::Max(It->StunnedUntil,Now()+GasStunDuration);
        It->GetCharacterMovement()->StopMovementImmediately();It->ForceNetUpdate();It->ClientFeedback(TEXT("Camera gas | Incapacitated"));
    }
    return true;
}
void ASPStickyCamera::MulticastCue_Implementation(bool bGas)
{
    if (bGas) ++GasCues;else ++NoiseCues;
    USoundBase* Sound=bGas?GasSound:NoiseSound;if (!Sound) return;
    USoundAttenuation* Att=NewObject<USoundAttenuation>(this);
    Att->Attenuation.bAttenuate=true;Att->Attenuation.bSpatialize=true;
    Att->Attenuation.AttenuationShape=EAttenuationShape::Sphere;
    Att->Attenuation.AttenuationShapeExtents=FVector(100);Att->Attenuation.FalloffDistance=bGas?800.f:1800.f;
    UGameplayStatics::SpawnSoundAtLocation(this,Sound,GetActorLocation(),FRotator::ZeroRotator,1.f,1.f,0.f,Att);
}
void ASPStickyCamera::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(ASPStickyCamera,GasReleasedAt);DOREPLIFETIME(ASPStickyCamera,LastNoiseAt);
}
