#pragma once
#include "CoreMinimal.h"
#include "Components/SkeletalMeshComponent.h"

namespace SPHandContacts
{
    // Centimetres in weapon aim space, independent of the rifle's body scale.
    inline const FVector RifleCenterFromPalm(1.f,-3.55f,0.f);
    inline const FVector LauncherCenterFromPalm(1.f,-4.1f,0.f);
    inline const FVector LauncherGripLocal(-1.f,0.f,-4.f);
    inline const FVector LauncherPalmLocal(18.f,0.f,-4.35f);
    // Socket offset to the support palm centre, below the actual handguard skin.
    inline const FVector SupportSocketToPalm(2.7f,3.f,.25f);
    inline FVector Palm(const USkeletalMeshComponent* Mesh)
    {return (Mesh->GetSocketLocation(TEXT("hand_r"))+Mesh->GetSocketLocation(TEXT("middle_01_r")))*.5f;}
    inline FVector PalmNormal(const USkeletalMeshComponent* Mesh)
    {
        const FVector Forward=Mesh->GetSocketLocation(TEXT("middle_01_r"))-Mesh->GetSocketLocation(TEXT("hand_r"));
        const FVector Across=Mesh->GetSocketLocation(TEXT("index_01_r"))-Mesh->GetSocketLocation(TEXT("pinky_01_r"));
        return FVector::CrossProduct(Forward,Across).GetSafeNormal();
    }
    inline FVector GrenadeCenter(const USkeletalMeshComponent* Mesh)
    {return Palm(Mesh)+(Mesh->GetSocketLocation(TEXT("middle_01_r"))-Mesh->GetSocketLocation(TEXT("hand_r"))).GetSafeNormal()+PalmNormal(Mesh)*4.45f;}
}
