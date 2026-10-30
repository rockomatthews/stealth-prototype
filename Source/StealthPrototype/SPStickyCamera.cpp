#include "Prototype.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

ASPStickyCamera::ASPStickyCamera()
{
    bReplicates=true;SetReplicateMovement(true);
    Housing=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CameraHousing"));SetRootComponent(Housing);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    Housing->SetStaticMesh(Sphere.Object);Housing->SetRelativeScale3D(FVector(.09f,.09f,.05f));
    Housing->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("StickyCameraView"));Camera->SetupAttachment(Housing);
    Camera->SetAbsolute(false,false,true);Camera->FieldOfView=85.f;
    InitialLifeSpan=60.f;
}
