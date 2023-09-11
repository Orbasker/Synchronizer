import re
import pandas as pd
def get_regex_result(barcode: str) -> str:
    if barcode is not None:
        regex_result = re.search(r"([1-9][0-9]*\d{6,8})", barcode)
        return regex_result.group() if regex_result else barcode
    return barcode


def define_barcode_type(regex_result: str) -> str:
    if regex_result and regex_result.startswith("103"):
        return "Jnet1"
    elif regex_result and regex_result[:3] in ["402", "750", "220", "470", "200"]:
        return "Jnet 0"
    else:
        return "Unknown"


def main():
    input_file = "inputBarcode.csv"
    output_file = "output.csv"

    # Read the input file
    df = pd.read_csv(input_file)

    # Get the regex result
    df["regex_result"] = df["barcode"].apply(get_regex_result)

    # Define the barcode type
    df["barcode_type"] = df["regex_result"].apply(define_barcode_type)

    # Save the results to the output file
    df.to_csv(output_file, index=False)


if __name__ == "__main__":
    main()
