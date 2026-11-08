#include "SPWarehouse.h"
#include "Prototype.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

ASPWarehouse::ASPWarehouse()
{
    bReplicates=true;bAlwaysRelevant=true;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("WarehouseRoot"));RootComponent->SetMobility(EComponentMobility::Static);
}
void ASPWarehouse::RebuildWarehouse() {Build();}
void ASPWarehouse::OnConstruction(const FTransform& Transform) {Super::OnConstruction(Transform);Build();}
void ASPWarehouse::Build()
{
    ClearInstanceComponents(true);for (const auto& Ref:Generated) if (auto* C=Ref.Get();IsValid(C)) C->DestroyComponent();Generated.Empty();
    TMap<FString,UHierarchicalInstancedStaticMeshComponent*> Groups;
    auto Add=[&](const FString& Mesh,const FString& Mat,const FVector& P,const FVector& Scale,const FRotator& R=FRotator::ZeroRotator,int32 Collision=0)
    {
        const FString Key=Mesh+Mat+FString::FromInt(Collision);UHierarchicalInstancedStaticMeshComponent*& C=Groups.FindOrAdd(Key);
        if (!C)
        {
            C=NewObject<UHierarchicalInstancedStaticMeshComponent>(this);C->SetupAttachment(RootComponent);C->SetMobility(EComponentMobility::Static);
            UStaticMesh* Asset=Mesh==TEXT("Cube")?LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")):LoadObject<UStaticMesh>(nullptr,*FString::Printf(TEXT("/Game/Warehouse/Meshes/%s.%s"),*Mesh,*Mesh));
            if (!Asset) Asset=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
            C->SetStaticMesh(Asset);
            if (!Mat.IsEmpty()) if (auto* M=LoadObject<UMaterialInterface>(nullptr,*FString::Printf(TEXT("/Game/Warehouse/Materials/M_%s.M_%s"),*Mat,*Mat)))
                for (int32 I=0;I<C->GetNumMaterials();++I) C->SetMaterial(I,M);
            C->SetCollisionProfileName(TEXT("BlockAll"));
            if (Collision==1) C->SetCollisionResponseToChannel(ECC_Visibility,ECR_Ignore); // Thin vent skins stop capsules, never bullets.
            if (Collision==2) C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            if (Collision==3) {C->SetCollisionResponseToAllChannels(ECR_Ignore);C->SetCollisionResponseToChannel(ECC_Pawn,ECR_Block);C->SetVisibility(false);}
            if (Mesh==TEXT("SM_Crate")) C->ComponentTags.Add(TEXT("Traversal"));
            AddInstanceComponent(C);C->RegisterComponent();Generated.Add(C);
        }
        C->AddInstance(FTransform(R,P,Scale));
    };
    auto Box=[&](const FString& Mat,FVector P,FVector Size,FRotator R=FRotator::ZeroRotator,int32 Collision=0){Add(TEXT("Cube"),Mat,P,Size/100.f,R,Collision);};
    Box(TEXT("ConcreteFloor"),FVector(0,0,-25),FVector(6000,4400,50));
    Box(TEXT("Concrete"),FVector(-3025,0,600),FVector(50,4400,1200));
    Box(TEXT("Concrete"),FVector(3025,0,600),FVector(50,4400,1200));
    Box(TEXT("Concrete"),FVector(0,2225,600),FVector(6000,50,1200));
    // Exactly one usable warehouse entrance from the merc respawn room.
    for (float X:{-1560.f,1560.f}) Box(TEXT("Concrete"),FVector(X,-2225,600),FVector(2880,50,1200));
    Box(TEXT("Concrete"),FVector(0,-2225,750),FVector(240,50,900));
    Box(TEXT("ConcreteFloor"),FVector(0,-2550,-25),FVector(900,650,50));
    for (float X:{-475.f,475.f}) Box(TEXT("Concrete"),FVector(X,-2550,160),FVector(50,650,320));
    Box(TEXT("Concrete"),FVector(0,-2900,160),FVector(1000,50,320));
    Box(TEXT("Concrete"),FVector(0,-2550,340),FVector(1000,700,40));
    // Perimeter catwalk, real stair treads, and railings with bullet-permeable gaps.
    for (int32 Side:{-1,1})
    {
        for (int32 I=-20;I<=20;++I)
        {
            Add(TEXT("SM_Grate"),TEXT(""),FVector(I*130,Side*1900,420),FVector(1.3,2.8,1));
            Add(TEXT("SM_Rail"),TEXT(""),FVector(I*130,Side*1758,425),FVector(1.3,1,1),FRotator::ZeroRotator,2);
        }
        for (int32 I=-13;I<=13;++I)
        {
            Add(TEXT("SM_Grate"),TEXT(""),FVector(Side*2800,I*130,420),FVector(2.8,1.3,1));
            Add(TEXT("SM_Rail"),TEXT(""),FVector(Side*2658,I*130,425),FVector(1.3,1,1),FRotator(0,90,0),2);
        }
        Box(TEXT("Steel"),FVector(0,Side*1758,470),FVector(5500,7,100),FRotator::ZeroRotator,3);
        Box(TEXT("Steel"),FVector(Side*2658,0,470),FVector(7,3400,100),FRotator::ZeroRotator,3);
        for (int32 I=0;I<14;++I)
        {
            const float X=Side*(-1800+I*35);const float H=(I+1)*30;
            Box(TEXT("Steel"),FVector(X,Side*1450,H*.5),FVector(35,210,H));
        }
        // Stair top landing connects to catwalk without an unwalkable jump.
        Box(TEXT("Steel"),FVector(Side*-1327,Side*1690,410),FVector(220,450,20));
    }
    // Columns, wall panels, exposed pipes, and roof trusses.
    for (int32 X=-2800;X<=2800;X+=700)
    {
        for (int32 S:{-1,1}) Add(TEXT("SM_Column"),TEXT(""),FVector(X,S*2130,0),FVector(1.5,1.5,11.5));
        for (int32 S:{-1,1})
        {
            const FVector A(X,0,1320),B(X,S*2190,1120);const FVector D=B-A;
            Add(TEXT("SM_Beam"),TEXT(""),(A+B)*.5,FVector(D.Size()/100,1.8,1.8),D.Rotation(),2);
            Add(TEXT("SM_Beam"),TEXT(""),FVector(X,S*1100,1120),FVector(22,1.3,1.3),FRotator(0,90,0),2);
        }
        for (int32 I=-2;I<=2;++I) Add(TEXT("SM_Beam"),TEXT(""),FVector(X,I*650,1215),FVector(6.5,1,1),FRotator(0,90,I%2?24:-24),2);
    }
    // Roof strips leave large real skylight openings: sunlight reaches the floor.
    for (int32 S:{-1,1})
    {
        for (int32 X=-2700;X<=2700;X+=600)
        {
            Box(TEXT("Roof"),FVector(X,S*1100,1220),FVector(170,2240,25),FRotator(0,0,S*5.2));
            for (int32 Y=450;Y<2200;Y+=850)
            {
                Box(TEXT("Glass"),FVector(X+300,S*Y,1320-Y*.091),FVector(410,800,2),FRotator(0,0,S*5.2),2);
                Box(TEXT("Steel"),FVector(X+270,S*Y,1320-Y*.091),FVector(430,22,18),FRotator::ZeroRotator,2);
            }
        }
        Box(TEXT("Roof"),FVector(0,S*2070,1130),FVector(6000,300,30));
        for (int32 Y=400;Y<2200;Y+=600) Add(TEXT("SM_Beam"),TEXT(""),FVector(0,S*Y,1320-Y*.091),FVector(60,1,1),FRotator::ZeroRotator,2);
    }
    FRandomStream Random(731);
    TArray<FVector2D> Banks;
    for (int32 Side:{-1,1}) for (float X:{650.f,1500.f,2400.f}) for (float Y:{-1450.f,-750.f,0.f,750.f,1450.f})
        if (!(Y==0.f && X<2000.f)) Banks.Add(FVector2D(Side*X,Y));
    for (const FVector2D Bank:Banks)
    {
        const int32 NX=Random.RandRange(2,3),NY=Random.RandRange(2,3);const float H=Random.RandRange(105,145);
        for (int32 I=0;I<NX;++I) for (int32 J=0;J<NY;++J)
        {
            const float X=Bank.X+(I-(NX-1)*.5f)*150,Y=Bank.Y+(J-(NY-1)*.5f)*130;
            Add(TEXT("SM_Pallet"),TEXT(""),FVector(X,Y,0),FVector(1.5,1.3,1));
            const int32 Layers=Random.RandRange(1,3);
            for (int32 K=0;K<Layers;++K) Add(TEXT("SM_Crate"),TEXT(""),FVector(X,Y,14+H*K),FVector(1.35,1.15,H/100),FRotator(0,Random.FRandRange(-2,2),0));
            if (Random.FRand()<.18) Add(TEXT("SM_Canvas"),TEXT(""),FVector(X,Y,14+H*Layers),FVector(1.1,.95,1),FRotator::ZeroRotator,2);
        }
    }
    // Low staggered boxes form real intermediate landings, not decoration.
    for (int32 Side:{-1,1}) for (float Y:{-1100.f,50.f,1100.f})
    {
        for (int32 I=0;I<4;++I) Add(TEXT("SM_Crate"),TEXT(""),FVector(Side*(430+I*135),Y,0),FVector(1.15,1.05,(70+I*50)/100.f));
        for (float X:{1100.f,1600.f}) for (int32 K=0;K<2;++K) Add(TEXT("SM_Crate"),TEXT(""),FVector(Side*X,Y,165*K),FVector(1.25,1.25,1.65));
        Add(TEXT("SM_Grate"),TEXT(""),FVector(Side*1350,Y,326),FVector(5.2,.9,1));
    }
    for (FVector P:{FVector(-2400,400,0),FVector(2400,-400,0),FVector(400,1500,0),FVector(-400,-1400,0)})
        for (int32 I=0;I<3;++I) Add(TEXT("SM_Barrel"),TEXT(""),P+FVector(I*65,0,0),FVector(.6,.6,1));
    // Floor safety lanes are painted strips, not glowing sci-fi markers.
    for (float X:{-450.f,450.f}) for (int32 Y=-1800;Y<1800;Y+=250) Box(TEXT("Yellow"),FVector(X,Y,.8),FVector(7,150,1),FRotator::ZeroRotator,2);
    for (float Y:{-1650.f,1650.f}) for (int32 X=-2400;X<2500;X+=250) Box(TEXT("Yellow"),FVector(X,Y,.8),FVector(150,7,1),FRotator::ZeroRotator,2);
    // Safe door, keypad and handle around the actual hackable actor at the center.
    for (float X:{-32.f,32.f}) Box(TEXT("Steel"),FVector(X,-47,60),FVector(4,4,112),FRotator::ZeroRotator,2);
    Box(TEXT("Steel"),FVector(13,-50,78),FVector(18,4,28),FRotator::ZeroRotator,2);
    for (int32 I=0;I<3;++I) for (int32 J=0;J<4;++J) Box(TEXT("Key"),FVector(8+I*5,-53,68+J*5),FVector(3,2,3),FRotator::ZeroRotator,2);
    Box(TEXT("Black"),FVector(-15,-53,65),FVector(4,8,35),FRotator(0,0,-15),2);
    // Future office transition: a closed facade, with solid warehouse wall behind it.
    Box(TEXT("Steel"),FVector(0,2196,125),FVector(210,8,250));
    Box(TEXT("Yellow"),FVector(0,2188,110),FVector(80,4,4),FRotator::ZeroRotator,2);
    // Three longitudinal ventilation runs and one cross-connection, six rope mouths.
    auto Vent=[&](float Fixed,bool AlongY,float Length)
    {
        for (float T=-Length*.5f+50;T<Length*.5f;T+=100)
        {
            FVector P=AlongY?FVector(Fixed,T,777):FVector(T,Fixed,777);
            Box(TEXT("Duct"),P,AlongY?FVector(180,100,6):FVector(100,180,6),FRotator::ZeroRotator,1);
            P.Z=888;Box(TEXT("Duct"),P,AlongY?FVector(180,100,6):FVector(100,180,6),FRotator::ZeroRotator,1);
            const bool Junction=AlongY?FMath::Abs(T)<110:(FMath::Abs(T)<110 || FMath::Abs(FMath::Abs(T)-2100)<110);
            if (!Junction) for (int32 S:{-1,1})
            {
                P=AlongY?FVector(Fixed+S*87,T,832.5):FVector(T,Fixed+S*87,832.5);
                Box(TEXT("Duct"),P,AlongY?FVector(6,100,105):FVector(100,6,105),FRotator::ZeroRotator,1);
            }
            // Raised seams and overhead suspension hangers add real geometry.
            if (FMath::RoundToInt(T)%300==50)
            {P=AlongY?FVector(Fixed,T,899):FVector(T,Fixed,899);Box(TEXT("Steel"),P,AlongY?FVector(195,4,5):FVector(4,195,5),FRotator::ZeroRotator,2);}
        }
    };
    for (float X:{-2100.f,0.f,2100.f}) Vent(X,true,2800);Vent(0,false,4200);
    for (float X:{-2100.f,0.f,2100.f}) for (int32 S:{-1,1})
    {
        const float Y=S*1420;
        Add(TEXT("SM_Beam"),TEXT(""),FVector(X,S*1430,905),FVector(1.4,.7,.7),FRotator(0,90,0),2);
        Box(TEXT("Steel"),FVector(X,S*1360,905),FVector(55,45,15),FRotator::ZeroRotator,2);
        Add(TEXT("SM_Grate"),TEXT(""),FVector(X+145,S*1440,835),FVector(1.6,1.0,1),FRotator(0,45,90),2);
        for (int32 Z=20;Z<880;Z+=100) Add(TEXT("SM_Rope"),TEXT(""),FVector(X,Y,Z),FVector(1.2,1.2,1),FRotator::ZeroRotator,2);
        // Floor knot at each rope, with no collision that could block shooting.
        Add(TEXT("SM_Rope"),TEXT(""),FVector(X,Y,6),FVector(1.2,1.2,.4),FRotator(0,0,90),2);
    }
    Box(TEXT("Steel"),FVector(-132,-2220,125),FVector(20,35,250));Box(TEXT("Steel"),FVector(132,-2220,125),FVector(20,35,250));Box(TEXT("Steel"),FVector(0,-2220,265),FVector(284,35,25));
    auto* EntryLight=NewObject<UPointLightComponent>(this);EntryLight->SetupAttachment(RootComponent);EntryLight->SetRelativeLocation(FVector(0,-2520,270));EntryLight->SetIntensity(7000);EntryLight->SetAttenuationRadius(700);EntryLight->SetLightColor(FLinearColor(1,.87,.72));EntryLight->SetCastShadows(false);AddInstanceComponent(EntryLight);EntryLight->RegisterComponent();Generated.Add(EntryLight);
    for (int32 I=0;I<8;++I)
    {
        const FVector P((I%4-1.5)*1300,(I/4?1:-1)*1050,1050);
        Add(TEXT("SM_Lamp"),TEXT(""),P,FVector(1),FRotator::ZeroRotator,2);
        auto* L=NewObject<UPointLightComponent>(this);L->SetupAttachment(RootComponent);L->SetRelativeLocation(P-FVector(0,0,35));L->SetIntensity(70000);L->SetAttenuationRadius(1750);L->SetLightColor(FLinearColor(1,.85,.66));L->SetCastShadows(false);AddInstanceComponent(L);L->RegisterComponent();Generated.Add(L);
    }
}
void ASPWarehouse::BeginPlay()
{
    Super::BeginPlay();Build();
    if (!HasAuthority()) return;
    for (float X:{-2100.f,0.f,2100.f})
    {
        auto* V=GetWorld()->SpawnActor<ASPVentRoute>(FVector(X,0,834),FRotator::ZeroRotator);V->HalfSize=FVector(84,1400,55);
        for (int32 S:{-1,1})
        {
            auto* R=GetWorld()->SpawnActor<ASPRope>(FVector(X,S*1420,0),FRotator(0,S<0?90:-90,0));R->Entry=FVector(X,S*1320,824);R->ForceNetUpdate();
        }
    }
    auto* Cross=GetWorld()->SpawnActor<ASPVentRoute>(FVector(0,0,834),FRotator::ZeroRotator);Cross->HalfSize=FVector(2100,84,55);
    GetWorld()->SpawnActor<ASPMercDoor>(FVector(0,-2200,0),FRotator::ZeroRotator);
}
ASPVentRoute::ASPVentRoute(){bReplicates=true;bAlwaysRelevant=true;RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("VentRoute"));}
bool ASPVentRoute::Contains(const FVector& P) const {const FVector D=P-GetActorLocation();return FMath::Abs(D.X)<HalfSize.X && FMath::Abs(D.Y)<HalfSize.Y && FMath::Abs(D.Z)<HalfSize.Z;}
void ASPVentRoute::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const {Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(ASPVentRoute,HalfSize);}
ASPRope::ASPRope(){bReplicates=true;bAlwaysRelevant=true;RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("RopeAnchor"));}
FVector ASPRope::Bottom() const {return GetActorLocation()-GetActorForwardVector()*40+FVector(0,0,90);}
FVector ASPRope::Top() const {FVector P=Bottom();P.Z=FloorHeight-60;return P;}
void ASPRope::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const {Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(ASPRope,Entry);DOREPLIFETIME(ASPRope,FloorHeight);}
ASPMercDoor::ASPMercDoor()
{
    bReplicates=true;bAlwaysRelevant=true;PrimaryActorTick.bCanEverTick=true;RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Entry"));
    Leaf=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SlidingDoor"));Leaf->SetupAttachment(RootComponent);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));Leaf->SetStaticMesh(Cube.Object);Leaf->SetRelativeScale3D(FVector(2.4,.12,2.5));Leaf->SetRelativeLocation(FVector(0,0,125));Leaf->SetCollisionProfileName(TEXT("BlockAll"));
}
void ASPMercDoor::BeginPlay(){Super::BeginPlay();if (auto* M=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Warehouse/Materials/M_Steel.M_Steel"))) Leaf->SetMaterial(0,M);}
void ASPMercDoor::Tick(float Delta)
{
    Super::Tick(Delta);
    if (HasAuthority())
    {
        bool Open=false;for (TActorIterator<ASPCharacter> It(GetWorld());It;++It) if (!It->IsSpy() && It->Health>0 && FVector::Dist2D(It->GetActorLocation(),GetActorLocation())<280) {Open=true;break;}
        if (bOpen!=Open) {bOpen=Open;ForceNetUpdate();}
    }
    Alpha=FMath::FInterpTo(Alpha,bOpen?1.f:0.f,Delta,8.f);Leaf->SetRelativeLocation(FVector(Alpha*270,0,125));
}
void ASPMercDoor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const {Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(ASPMercDoor,bOpen);}
