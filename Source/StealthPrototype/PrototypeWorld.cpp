#include "Prototype.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

ASPArena::ASPArena()
{
    bReplicates=true;bAlwaysRelevant=true;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("ArenaRoot"));RootComponent->SetMobility(EComponentMobility::Static);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto Box=[this](const TCHAR* Name,FVector P,FVector Size,UStaticMesh* Mesh,bool Traversable=false)
    {
        auto* C=CreateDefaultSubobject<UStaticMeshComponent>(Name);C->SetupAttachment(RootComponent);C->SetMobility(EComponentMobility::Static);
        C->SetStaticMesh(Mesh);C->SetRelativeLocation(P);C->SetRelativeScale3D(Size/100);
        C->SetCollisionProfileName(TEXT("BlockAll"));if (Traversable) C->ComponentTags.Add(TEXT("Traversal"));
    };
    Box(TEXT("Floor"),FVector(0,0,-25),FVector(3300,2500,50),Cube.Object);
    Box(TEXT("WestWall"),FVector(-1650,0,250),FVector(50,2500,500),Cube.Object);
    Box(TEXT("EastWall"),FVector(1650,0,250),FVector(50,2500,500),Cube.Object);
    Box(TEXT("NorthWall"),FVector(0,1250,250),FVector(3300,50,500),Cube.Object);
    Box(TEXT("SouthWall"),FVector(0,-1250,250),FVector(3300,50,500),Cube.Object);
    Box(TEXT("Roof"),FVector(0,0,520),FVector(3300,2500,35),Cube.Object);
    Box(TEXT("PartitionNorth"),FVector(0,825,220),FVector(80,800,440),Cube.Object);
    Box(TEXT("PartitionSouth"),FVector(0,-825,220),FVector(80,800,440),Cube.Object);
    Box(TEXT("CoverWestNorth"),FVector(-700,400,80),FVector(180,340,160),Cube.Object,true);
    Box(TEXT("CoverWestSouth"),FVector(-700,-400,80),FVector(180,340,160),Cube.Object,true);
    Box(TEXT("CoverEastNorth"),FVector(700,400,80),FVector(180,340,160),Cube.Object,true);
    Box(TEXT("CoverEastSouth"),FVector(700,-400,80),FVector(180,340,160),Cube.Object,true);
    Box(TEXT("SpyVault"),FVector(-350,0,45),FVector(100,350,90),Cube.Object,true);
    Box(TEXT("MercCover"),FVector(350,0,45),FVector(100,350,90),Cube.Object,true);
    // Raised route reachable by hanging/climbing, with no moving geometry.
    Box(TEXT("ClimbPlatformWest"),FVector(-1050,850,100),FVector(700,350,200),Cube.Object,true);
    Box(TEXT("ClimbPlatformEast"),FVector(1050,850,100),FVector(700,350,200),Cube.Object,true);
    Box(TEXT("Catwalk"),FVector(0,850,190),FVector(1500,180,20),Cube.Object,true);
    // 105 cm clearance: spy crouch is 84 cm; merc crouch is 120 cm.
    Box(TEXT("DuctTop"),FVector(0,-400,160),FVector(500,180,110),Cube.Object);
    Box(TEXT("DuctSideNorth"),FVector(0,-290,110),FVector(500,40,220),Cube.Object);
    Box(TEXT("DuctSideSouth"),FVector(0,-510,110),FVector(500,40,220),Cube.Object);
    for (int32 I=0;I<5;++I)
    {
        const FName Name(*FString::Printf(TEXT("WarehouseLight%d"),I));
        auto* Light=CreateDefaultSubobject<UPointLightComponent>(Name);Light->SetupAttachment(RootComponent);
        Light->SetRelativeLocation(FVector((I-2)*600, I%2? -250:250,420));
        Light->Intensity=I==2?20000:7000;Light->AttenuationRadius=I==2?850:1100;
        Light->LightColor=I==2?FColor(180,220,255):FColor(255,215,175);
    }
}
ASPTerminal::ASPTerminal()
{
    bReplicates=true;bAlwaysRelevant=true;
    auto* Mesh=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Terminal"));RootComponent=Mesh;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    Mesh->SetStaticMesh(Cube.Object);Mesh->SetRelativeScale3D(FVector(.7,.9,1.2));Mesh->SetCollisionProfileName(TEXT("BlockAll"));
    auto* Light=CreateDefaultSubobject<UPointLightComponent>(TEXT("StatusLight"));Light->SetupAttachment(RootComponent);
    Light->SetRelativeLocation(FVector(0,0,80));Light->Intensity=1000;Light->AttenuationRadius=250;Light->LightColor=FColor(80,220,255);
}
