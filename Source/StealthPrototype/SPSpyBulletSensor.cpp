#include "Prototype.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

ASPSpyBulletSensor::ASPSpyBulletSensor()
{
    bReplicates=true;SetReplicateMovement(true);InitialLifeSpan=45.f;
    Housing=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SpyBulletSensor"));SetRootComponent(Housing);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    Housing->SetStaticMesh(Sphere.Object);Housing->SetRelativeScale3D(FVector(.035f));
    Housing->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}
