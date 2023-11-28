import hashlib
import requests
import xml.etree.ElementTree as ET
from urllib.parse import unquote
import os


def create_base_url(participant_id):
    '''
    Returns a URL based on Peppol-lookup principles 
    :param participant_id: the PeppolID to look up
    :return: URL
    '''''
    # Create hash object
    hasher = hashlib.md5()

    # Convert to byte array and get hash
    participant_id_lower = participant_id.lower()
    hasher.update(participant_id_lower.encode('utf-8'))
    dbytes = hasher.digest()

    # Convert byte data to hex string
    hex_string = ''.join(f"{byte:02X}" for byte in dbytes)

    return f"http://b-{hex_string.lower()}.iso6523-actorid-upis.edelivery.tech.ec.europa.eu/iso6523-actorid-upis::{participant_id}"


def get_service_urns():
    return {
        "already_checked": False,
        "registered_in_dns": False,
        "urn:oasis:names:specification:ubl:schema:xsd:Catalogue-2::Catalogue##urn:fdc:peppol.eu:poacc:trns:catalogue:3::2.1": False,
        "urn:oasis:names:specification:ubl:schema:xsd:Catalogue-2::Catalogue##urn:fdc:peppol.eu:poacc:trns:punch_out:3::2.1": False,
        "urn:oasis:names:specification:ubl:schema:xsd:Order-2::Order##urn:fdc:peppol.eu:poacc:trns:order:3::2.1": False,
        "urn:oasis:names:specification:ubl:schema:xsd:OrderResponse-2::OrderResponse##urn:fdc:peppol.eu:poacc:trns:order_response:3::2.1": False,
        "urn:oasis:names:specification:ubl:schema:xsd:OrderResponse-2::OrderResponse##urn:fdc:peppol.eu:poacc:trns:order_agreement:3::2.1": False,
        "urn:oasis:names:specification:ubl:schema:xsd:DespatchAdvice-2::DespatchAdvice##urn:fdc:peppol.eu:poacc:trns:despatch_advice:3::2.1": False,
        "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1": False,
        "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2::CreditNote##urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1": False,
        "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100::CrossIndustryInvoice##urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0::D16B": False,
    }


def published_services(participant_id):
    '''
    Makes a lookup into Peppol SML/SMP and returns the registered services
    :param participant_id: The PeppolID to lookup
    :return: A dictionary with each service as key and value true/false. Returns None in case the id isn't registered in Peppol
    '''
    # Create dictionary
    service_urns = get_service_urns()

    try:
        # Get the service metadata from the Peppol network
        base_url = create_base_url(participant_id)  # Assuming you have a create_base_url function
        response = requests.get(base_url)
        response.raise_for_status()

        xml_service_group = ET.fromstring(response.content)
        ns = {'ns2': 'http://busdox.org/serviceMetadata/publishing/1.0/'}
        service_urns["registered_in_dns"] = True
        service_urns["already_checked"] = True

        for service in xml_service_group.findall('.//ns2:ServiceMetadataReferenceCollection/ns2:ServiceMetadataReference', ns):
            url = unquote(service.attrib.get('href', ''))

            for pub_service in service_urns:
                if pub_service in url:
                    service_urns[pub_service] = True
                    break

    except Exception as e:
        service_urns["registered_in_dns"] = False
        service_urns["already_checked"] = True

    return service_urns


def line_value_to_participant_id(line_value):

    participant_id = ""

    if len(line_value) == 10:
        # Add prefix "0007:" if the value is 10 digits long
        participant_id = "0007:" + line_value
    elif len(line_value) == 13:
        # Add prefix "0088:" if the value is 13 digits long
        participant_id = "0088:" + line_value

    return participant_id


def main():
    participants_to_check = {}
    number_of_lines = 0
    while True:
        filepath_in = input("Please enter the file path to a text with participant identifiers file: ")

        # Check if the file exists
        if os.path.isfile(filepath_in):
            try:
                # Creating new file path with _out suffix
                base, ext = os.path.splitext(filepath_in)
                filepath_out = base + "_out" + ext

                with open(filepath_in, 'r') as file:
                    for line in file:
                        # Remove any trailing whitespace including newline characters
                        number_of_lines += 1  # calc num of lines

                        # Add schemeid (suffix) to the identifier
                        participant_id = line_value_to_participant_id(line.strip())

                        # Populate a dictionary for all unique participants with an empty service dictionary
                        if participant_id != "":
                            participants_to_check[participant_id] = get_service_urns()

                    # start over and go through the list, retrieve services for all participants
                    file.seek(0)

                    # Open output file for the result
                    with open(filepath_out, 'w') as file_out:
                        # output the column headings for the result
                        column_heading = "PeppolID;" + ';'.join(str(key) for key in get_service_urns())
                        file_out.write(f"{column_heading}\n")

                        # go through each line and output the result
                        for line_number, line in enumerate(file, start=1):
                            participant_id = line_value_to_partipant_id(line.strip())

                            if participant_id != "":
                                # check if the services has already been retrieved for the participant (if it is a duplicate row)
                                if not participants_to_check[participant_id]["already_checked"]:
                                    participants_to_check[participant_id] = published_services(participant_id)

                                lookup_result = participant_id + ";" + ";".join(str(value) for value in participants_to_check[participant_id].values())
                            else:
                                lookup_result = ""

                            print(f"\rParticipant {line_number} of {number_of_lines} verified", end="")

                            file_out.write(f"{lookup_result}\n")
                            file_out.flush()

                print("")
                print(f"Result of lookups saved as {filepath_out}")
                break  # Exit the loop after successful processing
            except Exception as e:
                print(f"An error occurred while processing the file: {e}")
        else:
            print("Invalid file path. Please try again.")


if __name__ == "__main__":
    main()
