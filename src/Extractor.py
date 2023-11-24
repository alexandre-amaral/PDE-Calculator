import json
import requests

class NoSubsectionException(Exception): pass

class Extractor:
    __data: dict = {}
    substance: str

    def __init__(self, substance: str):
        self.substance = substance
        self.__data["name"] = self.substance
        self.cid = Extractor.fetch_cid(self.substance)
        toxicity_info = Extractor.fetch_toxicity_info(self.cid)
        
        self.__data["cid"] = self.cid
        self.__data.update(toxicity_info)

    @staticmethod
    def assemble_pug_rest_url(substance: str):
        return f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{substance}/JSON"

    @staticmethod
    def assemble_pug_soap_url(cid: int):
        return f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON"

    @staticmethod
    def fetch_cid(substance: str) -> int:
        url = Extractor.assemble_pug_rest_url(substance)
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Couldn't fetch CID from PUG REST.")
        response_obj = response.json()
        return int(response_obj["PC_Compounds"][0]["id"]["id"]["cid"])

    @staticmethod
    def search_subsections(sections: list, heading_key: str, value: str) -> int:
        headers = [x[heading_key] for x in sections]
        if value not in headers:
            raise NoSubsectionException()
        return headers.index(value)

    @staticmethod
    def fetch_toxicity_info(cid: int) -> dict:
        url = Extractor.assemble_pug_soap_url(cid)
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Couldn't ping PUG SOAP.")
        response_obj = response.json()
        sections = response_obj["Record"]["Section"]

        summary = ""
        acute_effects_data = ""

        try:
            toxicity_section_index = Extractor.search_subsections(sections, "TOCHeading", "Toxicity")
            toxicity_subsections = sections[toxicity_section_index]["Section"]
            toxicological_information_index = Extractor.search_subsections(toxicity_subsections, "TOCHeading", "Toxicological Information")
            toxicological_information_section = toxicity_subsections[toxicological_information_index]["Section"]

            # Extracting Toxicity Summary
            try:
                summary_index = Extractor.search_subsections(toxicological_information_section, "TOCHeading", "Toxicity Summary")
                summary_section = toxicological_information_section[summary_index]
                summary = summary_section["Information"][0]["Value"]["StringWithMarkup"][0]["String"]
            except NoSubsectionException:
                summary = ""

            # Extracting Acute Effects
            try:
              toxicity_values_index = Extractor.search_subsections(toxicological_information_section, "TOCHeading", "Non-Human Toxicity Values")
              toxicity_values_section = toxicological_information_section[toxicity_values_index]
              toxicity_values = toxicity_values_section
            

            except NoSubsectionException:
                toxicity_values = ""

        except NoSubsectionException:
            toxicological_information_section = ""

        return {
            
            "summary": summary,
            "toxicity_values": toxicity_values
        }

    @property
    def data(self) -> dict:
        return self.__data

    def get_JSON(self) -> str:
        return json.dumps(self.data)




