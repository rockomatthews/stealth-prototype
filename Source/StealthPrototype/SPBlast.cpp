#include "Prototype.h"
#include "SPBlast.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

namespace {
struct FBlastPart {const TCHAR* Name;const TCHAR* Bone;FVector Center;};
const FBlastPart Parts[]={
#include "SPBlastParts.inl"
};
}
void SPBlast::LoadAssets(ASPGrabGrenade* G)
{
    for (const auto& Part:Parts)
    {
        const FString Path=FString::Printf(TEXT("/Game/Characters/Grab/Blast/SM_Merc%s.SM_Merc%s"),Part.Name,Part.Name);
        ConstructorHelpers::FObjectFinder<UStaticMesh> Mesh(*Path);G->FragmentAssets.Add(Mesh.Object);
    }
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cloud(TEXT("/Engine/BasicShapes/Plane.Plane"));G->CloudAsset=Cloud.Object;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Dust(TEXT("/Game/Characters/Grab/Blast/M_BlastDustSoft.M_BlastDustSoft"));G->DustMaterial=Dust.Object;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Cut(TEXT("/Game/Characters/Grab/Blast/M_CutInterior.M_CutInterior"));G->CutMaterial=Cut.Object;
}
void ASPGrabGrenade::OnRep_Exploded()
{
    if (BlastStartedAt>=0) return;
    BlastStartedAt=GetWorld()->GetTimeSeconds();Housing->SetVisibility(false);Lever->SetVisibility(false);SafetyPin->SetVisibility(false);
    if (GetNetMode()==NM_DedicatedServer) return;
    // Every client receives one explosion state and builds its own cosmetic physics.
    // These fragments never block players, bullets or damage queries.
    FRandomStream Random(7321+Epoch);
    if (bPlanted && IsValid(Victim) && Victim->GetMesh()->GetSkeletalMeshAsset())
    {
        auto* Body=Victim->GetMesh();const FReferenceSkeleton& Ref=Body->GetSkeletalMeshAsset()->GetRefSkeleton();
        for (int32 I=0;I<UE_ARRAY_COUNT(Parts);++I)
        {
            if (!FragmentAssets.IsValidIndex(I) || !FragmentAssets[I]) continue;
            const auto& Part=Parts[I];const int32 Bone=Ref.FindBoneIndex(Part.Bone);if (Bone==INDEX_NONE) continue;
            FTransform Bind=Ref.GetRefBonePose()[Bone];
            for (int32 Parent=Ref.GetParentIndex(Bone);Parent!=INDEX_NONE;Parent=Ref.GetParentIndex(Parent)) Bind=Bind*Ref.GetRefBonePose()[Parent];
            const FTransform Pose=Body->GetSocketTransform(Part.Bone);
            const FVector Position=Pose.TransformPosition(Bind.InverseTransformPosition(Part.Center));
            auto* Piece=NewObject<UStaticMeshComponent>(this);Piece->SetMobility(EComponentMobility::Movable);Piece->SetStaticMesh(FragmentAssets[I]);
            Piece->SetCollisionEnabled(ECollisionEnabled::PhysicsOnly);Piece->SetCollisionResponseToAllChannels(ECR_Ignore);Piece->SetCollisionResponseToChannel(ECC_WorldStatic,ECR_Block);
            Piece->SetCastShadow(true);Piece->RegisterComponent();Piece->SetWorldLocationAndRotation(Position,Pose.GetRotation()*Bind.GetRotation().Inverse());
            Piece->SetSimulatePhysics(true);Piece->SetMassOverrideInKg(NAME_None,5.f,true);Piece->SetLinearDamping(.35f);Piece->SetAngularDamping(.6f);
            FVector Direction=(Position-GetActorLocation()).GetSafeNormal();Direction.Z=FMath::Abs(Direction.Z)*.5f+.45f;
            Piece->SetPhysicsLinearVelocity(Direction*Random.FRandRange(330.f,650.f)+FVector(Random.FRandRange(-120,120),Random.FRandRange(-120,120),130));
            Piece->SetPhysicsAngularVelocityInDegrees(Random.VRand()*Random.FRandRange(150,400));++BodyFragmentCount;
        }
    }
    for (int32 I=0;I<24;++I)
    {
        auto* Cloud=NewObject<UStaticMeshComponent>(this);Cloud->SetMobility(EComponentMobility::Movable);Cloud->SetStaticMesh(CloudAsset);
        Cloud->SetCollisionEnabled(ECollisionEnabled::NoCollision);Cloud->SetCastShadow(false);Cloud->RegisterComponent();
        if (DustMaterial) {auto* M=UMaterialInstanceDynamic::Create(DustMaterial,Cloud);M->SetVectorParameterValue(TEXT("DustColor"),bPlanted && I<3?FLinearColor(.19f,.012f,.014f):I<8?FLinearColor(.025f,.022f,.02f):FLinearColor(.16f,.13f,.09f));Cloud->SetMaterial(0,M);}
        BlastClouds.Add(Cloud);
    }
    BlastLight=NewObject<UPointLightComponent>(this);BlastLight->SetMobility(EComponentMobility::Movable);BlastLight->RegisterComponent();BlastLight->SetWorldLocation(GetActorLocation()+FVector(0,0,15));
    BlastLight->SetLightColor(FLinearColor(1,.46f,.17f));BlastLight->SetIntensity(180000.f);BlastLight->SetAttenuationRadius(450);BlastLight->SetCastShadows(false);
    // Very brief irregular spark streaks replace the opaque glowing fireball.
    UMaterialInterface* Flash=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Characters/Grab/M_Blast.M_Blast"));
    for (int32 I=0;I<12;++I)
    {
        auto* Spark=NewObject<UStaticMeshComponent>(this);Spark->SetMobility(EComponentMobility::Movable);Spark->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere")));Spark->SetMaterial(0,Flash);Spark->SetCollisionEnabled(ECollisionEnabled::NoCollision);Spark->SetCastShadow(false);Spark->RegisterComponent();BlastClouds.Add(Spark);
    }
    UMaterialInterface* FireMaterial=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Characters/Grab/Blast/M_BlastFireSoft.M_BlastFireSoft"));
    for (int32 I=0;I<14;++I)
    {
        auto* Fire=NewObject<UStaticMeshComponent>(this);Fire->SetMobility(EComponentMobility::Movable);Fire->SetStaticMesh(CloudAsset);Fire->SetCollisionEnabled(ECollisionEnabled::NoCollision);Fire->SetCastShadow(false);Fire->RegisterComponent();
        if (FireMaterial) Fire->SetMaterial(0,UMaterialInstanceDynamic::Create(FireMaterial,Fire));
        BlastFire.Add(Fire);
    }
    if (bPlanted) for (int32 I=0;I<64;++I)
    {
        auto* Blood=NewObject<UStaticMeshComponent>(this);Blood->SetMobility(EComponentMobility::Movable);Blood->SetStaticMesh(CloudAsset);Blood->SetCollisionEnabled(ECollisionEnabled::NoCollision);Blood->SetCastShadow(false);Blood->RegisterComponent();Blood->SetWorldLocation(GetActorLocation());
        if (DustMaterial) {auto* M=UMaterialInstanceDynamic::Create(DustMaterial,Blood);M->SetVectorParameterValue(TEXT("DustColor"),FLinearColor(.24f,.0015f,.003f));M->SetScalarParameterValue(TEXT("Density"),.95f);Blood->SetMaterial(0,M);}
        BlastBlood.Add(Blood);BloodVelocity.Add(Random.VRand()*Random.FRandRange(220.f,850.f)+FVector(0,0,140));BloodDeposited.Add(false);
    }
    if (USoundBase* Sound=LoadObject<USoundBase>(nullptr,TEXT("/Game/Characters/Grab/GrenadeBlast.GrenadeBlast"))) UGameplayStatics::PlaySoundAtLocation(this,Sound,GetActorLocation());
    UpdateBlast(0);
}
void ASPGrabGrenade::UpdateBlast(float Delta)
{
    const float Age=FMath::Max(0.f,GetWorld()->GetTimeSeconds()-BlastStartedAt);
    if (BlastLight) {BlastLight->SetIntensity(180000.f*FMath::Square(FMath::Clamp(1.f-Age/.32f,0.f,1.f)));BlastLight->SetVisibility(Age<.32f);}
    auto FaceCamera=[&](UStaticMeshComponent* C,const FVector& Position,float Roll)
    {if (auto* Camera=UGameplayStatics::GetPlayerCameraManager(this,0)) C->SetWorldRotation((FRotationMatrix::MakeFromZ(Camera->GetCameraLocation()-Position).ToQuat()*FQuat(FVector::UpVector,Roll)).Rotator());};
    for (int32 I=0;I<BlastFire.Num();++I)
    {
        auto* Fire=BlastFire[I].Get();const float Life=.25f+(I%5)*.045f;Fire->SetVisibility(Age<Life);
        const float A=I*2.399963f;const FVector Out(FMath::Cos(A),FMath::Sin(A),.3f+(I%3)*.35f);
        const FVector Pos=GetActorLocation()+Out*(10.f+(150.f+(I%4)*45.f)*Age)+FVector(0,0,Age*80.f);Fire->SetWorldLocation(Pos);FaceCamera(Fire,Pos,A);
        const float Size=17.f+(I%3)*6.f+40.f*FMath::Sqrt(Age);Fire->SetWorldScale3D(FVector(Size/50.f,Size/50.f,1));
        if (auto* M=Cast<UMaterialInstanceDynamic>(Fire->GetMaterial(0)))
        {M->SetVectorParameterValue(TEXT("DustColor"),FMath::Lerp(FLinearColor(5,2,.1f),FLinearColor(1,.12f,.005f),FMath::Clamp(Age/Life,0.f,1.f)));M->SetScalarParameterValue(TEXT("Density"),FMath::Clamp(1.f-Age/Life,0.f,1.f)*.7f);}
    }
    for (int32 I=0;I<BlastBlood.Num();++I)
    {
        auto* Blood=BlastBlood[I].Get();if (BloodDeposited[I]) continue;
        const FVector Pos=GetActorLocation()+BloodVelocity[I]*Age-FVector(0,0,490.f*Age*Age);
        FHitResult Hit;FCollisionQueryParams Params(SCENE_QUERY_STAT(BlastBlood),false,this);if (Victim) Params.AddIgnoredActor(Victim);if (Captor) Params.AddIgnoredActor(Captor);
        if (GetWorld()->LineTraceSingleByObjectType(Hit,Blood->GetComponentLocation(),Pos,FCollisionObjectQueryParams(ECC_WorldStatic),Params))
        {
            BloodDeposited[I]=true;Blood->SetWorldLocation(Hit.ImpactPoint+Hit.ImpactNormal*.6f);Blood->SetWorldRotation(FRotationMatrix::MakeFromZ(Hit.ImpactNormal).Rotator());
            const float Size=.12f+(I%7)*.035f;Blood->SetWorldScale3D(FVector(Size,Size*.65f,1));
        }
        else {Blood->SetWorldLocation(Pos);FaceCamera(Blood,Pos,I);const float Size=.025f+(I%5)*.012f;Blood->SetWorldScale3D(FVector(Size,Size*2.5f,1));Blood->SetVisibility(Age<2.2f);}
    }
    for (int32 I=0;I<BlastClouds.Num();++I)
    {
        auto* C=BlastClouds[I].Get();if (!C) continue;
        const float Angle=I*2.399963f;
        const FVector Out(FMath::Cos(Angle),FMath::Sin(Angle),.2f);
        if (I>=24)
        {C->SetVisibility(Age<.08f);C->SetWorldLocation(GetActorLocation()+Out*(Age*1500));C->SetWorldRotation(Out.Rotation());C->SetWorldScale3D(FVector(.10f+Age*1.5f,.008f,.008f));continue;}
        const bool Ground=I>=8;const float Radius=(Ground?60.f:28.f)*(1.f-FMath::Exp(-Age*9.f))+Age*(Ground?65.f:20.f);
        FVector Position=GetActorLocation()+Out*Radius;
        Position.Z=Ground?FMath::Max(5.f,GetActorLocation().Z-85.f)+Age*17.f:GetActorLocation().Z+Age*(24+I*3.f);
        C->SetWorldLocation(Position);const float Size=(Ground?16.f:22.f)+Age*(Ground?24.f:28.f);
        C->SetWorldScale3D(FVector(Size/35.f,Size/35.f,1.f));C->SetVisibility(Age<2.5f);
        if (auto* Camera=UGameplayStatics::GetPlayerCameraManager(this,0))
            C->SetWorldRotation((FRotationMatrix::MakeFromZ(Camera->GetCameraLocation()-Position).ToQuat()*FQuat(FVector::UpVector,Angle)).Rotator());
        if (auto* M=Cast<UMaterialInstanceDynamic>(C->GetMaterial(0))) M->SetScalarParameterValue(TEXT("Density"),(Ground?.32f:.50f)*FMath::Clamp(Age/.05f,0.f,1.f)*FMath::Clamp(1.f-Age/(bPlanted && I<3?.35f:2.5f),0.f,1.f));
    }
}
