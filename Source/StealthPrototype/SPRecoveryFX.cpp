#include "SPRecoveryFX.h"
#include "Prototype.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

USPRecoveryFX::USPRecoveryFX()
{
    PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.TickGroup=TG_PostPhysics;
    SetMobility(EComponentMobility::Movable);
    SetCollisionEnabled(ECollisionEnabled::NoCollision);SetGenerateOverlapEvents(false);
    SetCanEverAffectNavigation(false);SetCastShadow(false);SetOwnerNoSee(true);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    SetStaticMesh(Cube.Object);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Material(TEXT("/Game/Prototype/FX/M_RecoveryArc.M_RecoveryArc"));
    if (Material.Succeeded()) SetMaterial(0,Material.Object);
}
void USPRecoveryFX::BeginPlay()
{
    Super::BeginPlay();
    if (auto* P=Cast<ASPCharacter>(GetOwner())) AddTickPrerequisiteComponent(P->GetMesh());
    if (auto* M=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Prototype/FX/M_RecoveryArc.M_RecoveryArc"))) ArcMaterial=CreateDynamicMaterialInstance(0,M);
    for (int32 I=0;I<48;++I) AddInstance(FTransform(FVector::ZeroVector));
    SetVisibility(false);
}
void USPRecoveryFX::TickComponent(float Delta,ELevelTick Tick,FActorComponentTickFunction* Function)
{
    Super::TickComponent(Delta,Tick,Function);
    auto* P=Cast<ASPCharacter>(GetOwner());const bool Active=P && P->HasRecoveryShield();
    SetVisibility(Active);Glow=0;if (!Active) return;
    SetOwnerNoSee(!P->IsInspectingAppearance());
    const float T=P->ServerNow();const int32 Frame=FMath::FloorToInt(T*18.f);
    Glow=(.7f+.3f*FMath::Sin(T*31.f))*FMath::Clamp((P->RecoveryShield.Until-T)/.35f,0.f,1.f);
    if (ArcMaterial) ArcMaterial->SetScalarParameterValue(TEXT("Power"),Glow*16.f);
    const TCHAR* A[]={TEXT("head"),TEXT("head"),TEXT("spine_03"),TEXT("spine_03"),TEXT("upperarm_l"),TEXT("upperarm_r"),TEXT("pelvis"),TEXT("pelvis"),TEXT("calf_l"),TEXT("calf_r"),TEXT("hand_l"),TEXT("hand_r")};
    const TCHAR* B[]={TEXT("clavicle_l"),TEXT("clavicle_r"),TEXT("pelvis"),TEXT("pelvis"),TEXT("hand_l"),TEXT("hand_r"),TEXT("calf_l"),TEXT("calf_r"),TEXT("foot_l"),TEXT("foot_r"),TEXT("spine_03"),TEXT("spine_03")};
    for (int32 Arc=0;Arc<12;++Arc)
    {
        const FVector Side=P->GetActorRightVector()*(Arc%2?1.f:-1.f);
        const float Radius=(Arc<4 || Arc==6 || Arc==7)?23.f:13.f;
        const FVector Offset=(Side+P->GetActorForwardVector()*((Arc/2)%2?-1.f:1.f)).GetSafeNormal()*Radius;
        const FVector Start=P->GetMesh()->GetSocketLocation(A[Arc])+Offset,End=P->GetMesh()->GetSocketLocation(B[Arc])+Offset;
        FVector Previous=Start;
        for (int32 Segment=1;Segment<=4;++Segment)
        {
            const float Hash=FMath::Sin(Frame*9.13f+Arc*17.2f+Segment*6.7f);
            const FVector Point=FMath::Lerp(Start,End,Segment/4.f)+(Segment==4?FVector::ZeroVector:Side*(Hash*7.f)+FVector(0,0,Hash*4.f));
            const FVector D=Point-Previous;
            UpdateInstanceTransform(Arc*4+Segment-1,FTransform(D.Rotation(),(Point+Previous)*.5f,FVector(D.Size()/100.f,.006f,.006f)),true,Arc==11 && Segment==4,true);
            Previous=Point;
        }
    }
    UpdateBounds();
}
