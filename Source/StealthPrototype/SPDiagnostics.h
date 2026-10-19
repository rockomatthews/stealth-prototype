#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SPDiagnostics.generated.h"
UCLASS()
class STEALTHPROTOTYPE_API USPDiagnostics : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable) static FString RuntimeReport();
    UFUNCTION(BlueprintCallable) static FString Exercise(int32 PlayerIndex,const FString& Action);
};
