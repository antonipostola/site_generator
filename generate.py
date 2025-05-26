from os.path import exists, isfile
import os, shutil
import copy

from bs4 import BeautifulSoup
from bs4 import Tag, Comment
from bs4.element import PageElement



# locations for the generator

PREPROCESSED_SITE_LOCATION = "./site/"
TEMPLATE_LOCATION = "./templates/"
RESOURCE_LOCATION = "./resource/"
GENERATION_LOCATION = "./generated_site/"


# languages

LANGUAGES: list[str] = ["en", "pl"]


# site names for each language

LANGUAGE_SITE_NAMES: dict[str, dict[str, str]] = {
    "example": {
        "en": "example",
        "pl": "przykład",
    }
}

def get_language_site_name(base_site_name: str, lang: str):

    if not base_site_name in LANGUAGE_SITE_NAMES:
        return base_site_name

    if not lang in LANGUAGE_SITE_NAMES[base_site_name]:
        return base_site_name

    return LANGUAGE_SITE_NAMES[base_site_name][lang]



# generation error message functions

def fail(msg: str):
    print(f"\nERROR {msg}")
    quit()

def warn(msg: str):
    print(f"\nWARNING {msg}")



# gets dict[str, str] of a tags attributes
def get_attribute_dict(tag: Tag) -> dict[str, str]:
    result: dict[str, str] = {}

    for key, value in tag.attrs.items():
        result[key] = str(value)

    return result


# these are to decrease reprocessing the templates

templates: dict[str, BeautifulSoup] = {}
templates_being_parsed: list[str] = []

# expands a <CustomTemplate> tag, the template insert being None means this is being added as a parsed template to the templates dictionary

def expand_template( template_html_location: str, template_body: list[PageElement]|None = None, template_vars: dict[str, str]|None = None ) -> PageElement:
    global templates, templates_being_parsed


    # check validity of template path

    def is_in_template_path(path: str):
        return os.path.commonpath( [os.path.normpath(path), os.path.normpath(TEMPLATE_LOCATION)] ) == os.path.normpath(TEMPLATE_LOCATION)

    if not is_in_template_path(template_html_location):
        template_html_location = os.path.join(TEMPLATE_LOCATION, template_html_location)
        if not is_in_template_path(template_html_location):
            fail(f"'{template_html_location}' reaches outside the '{TEMPLATE_LOCATION}' folder.")


    if not os.path.exists(template_html_location):
        fail(f"There is no template at '{template_html_location}'.")



    # handle parsing argument
    
    if template_body == None:
        if not template_html_location in templates:
            templates_being_parsed.append(template_html_location)
        else:
            return templates[template_html_location]



    # set template variables to be an empty dictionary if unset

    if template_vars == None:
        template_vars = {}



    # create the BeautifulSoup tree, use semi-processed template if it exists

    if template_html_location in templates:
        soup = copy.deepcopy(templates[template_html_location])
    else:
        with open(f"{template_html_location}") as f:
            contents = f.read()

        print(f"Parsing {template_html_location}")

        soup = BeautifulSoup(contents, "html.parser")



    # insert the body of the template

    for template_body_tag in soup.find_all("customtemplatebody"):
        assert isinstance(template_body_tag, Tag)

        if template_body != None:
            _ = template_body_tag.insert_before(*template_body)
            template_body_tag.decompose()



    # subsitute the template variables

    for template_var_tag in soup.find_all("customtemplatevar"):
        assert isinstance(template_var_tag, Tag)

        if template_body != None:

            var_name = str(template_var_tag.get("name"))

            if var_name == "None":
                fail(f"({template_html_location}): 'CustomTemplate' tags must have a 'name' attribute.")

            elif var_name not in template_vars:
                warn(f"({template_html_location}): template variable '{var_name}' went unused.")
            else:
                _ = template_var_tag.insert_before(template_vars[var_name])

            template_var_tag.decompose()



    # expand other templates if present in this one

    for template_tag in soup.find_all("customtemplate"):
        assert isinstance(template_tag, Tag)

        other_template_loc = str(template_tag.get("location"))

        if other_template_loc == "None":
            fail(f"({template_html_location}): 'CustomTemplate' tags must have a 'location' attribute set to a valid template path.")

        if not other_template_loc.startswith(TEMPLATE_LOCATION):
            other_template_loc = TEMPLATE_LOCATION + other_template_loc

        if other_template_loc in templates_being_parsed:
            fail(f"({template_html_location}): Cyclic template usage detected when trying to use the template at '{other_template_loc}'.")

        _ = template_tag.insert_before( expand_template(other_template_loc, list(template_tag.children), get_attribute_dict(template_tag)) )

        template_tag.decompose()



    # remove parsing status

    if template_body == None and not template_html_location in templates:
        templates_being_parsed.remove(template_html_location)
        templates[template_html_location] = soup


    # return expanded template

    return soup



# generates the final site

def generate_html(raw_html_location: str):

    # final html for different languages

    generated_html: dict[str, BeautifulSoup] = {}
    for lang in LANGUAGES:
        generated_html[lang] = BeautifulSoup(f"<!DOCTYPE html>\n<html lang=\"{lang}\"></html>", "html.parser")


    # keeps track of the place in the html tree being edited for each language

    tag_edited: dict[str, Tag] = {}

    for lang in LANGUAGES:
        language_html_tag = generated_html[lang].find("html")
        assert isinstance(language_html_tag, Tag)

        tag_edited[lang] = language_html_tag



    # recursive function parses all the elements and adds them to the respective language

    def parse_element(element: PageElement, parent_lang: str="None"):

        # add tags to the tree(s)

        if isinstance(element, Tag):

            # get relevant languages

            element_lang = str(element.get("languagesite"))

            langs_affected: list[str] = []

            if element_lang == "None": # unset

                if parent_lang == "None":
                    langs_affected = LANGUAGES
                else:
                    langs_affected = [parent_lang]

            else: # set

                if not element_lang in LANGUAGES:
                    fail(f"({raw_html_location}): '{element_lang}' is not a supported language.")

                elif parent_lang != "None" and element_lang != parent_lang:
                    fail(f"({raw_html_location}): <{element.name}>'s lang attribute '{element_lang}' does not match the inherited value of '{parent_lang}'.")

                else:
                    langs_affected = [element_lang]



            # add the tag to each relevant language site and remove the custom 'LanguageSite' attribute

            for lang in langs_affected:
                # creates childless version of the tag to prevent them being appended
                childless = copy.deepcopy(element)
                childless.clear() 

                del childless["languagesite"]


                # add the tag to the new html tree
                _ = tag_edited[lang].append(childless)

                # set the focus to the tag
                tag_edited[lang] = childless


            # parse the children

            for child in element.children:
                parse_element(child, parent_lang if element_lang == "None" else element_lang)


            # once the children are parsed, set the focus back to the parent

            for lang in langs_affected:
                previous_edited = tag_edited[lang].parent
                assert previous_edited != None
                tag_edited[lang] = previous_edited



        # add the non comment text elements to the tree(s)

        elif not isinstance(element, Comment):
            langs_affected = LANGUAGES if parent_lang == "None" else [parent_lang]
            for lang in langs_affected:
                _ = tag_edited[lang].append(copy.deepcopy(element))




    # read the html file contents

    with open(f"{raw_html_location}") as f:
        contents = f.read()

    print(f"Parsing {raw_html_location}")

    soup = BeautifulSoup(contents, "html.parser")



    # expand the templates present

    for template_tag in soup.find_all("customtemplate"):
        assert isinstance(template_tag, Tag)

        template_loc = str(template_tag.get("location"))

        if template_loc == "None":
            fail(f"({raw_html_location}): 'CustomTemplate' tags must have a 'location' attribute set to a valid template path.")

        _ = template_tag.insert_before( expand_template(template_loc, list(template_tag.children), get_attribute_dict(template_tag)) )
        template_tag.decompose()



    # parse the elements and begin adding them to their designated language sites

    for child in soup:
        parse_element(child)





    # create the html strings

    result: dict[str, str] = {}
    for lang in LANGUAGES:
        result[lang] = str(generated_html[lang])


    # useful path variables

    genloc: dict[str, str] = {}

    for lang in LANGUAGES:

        path = os.path.normpath(raw_html_location)

        path_segments = path.split(os.sep)
        path_segments[0] = lang # replaces the PREPROCESSED_SITE_LOCATION with the language

        for i in range(1, len(path_segments)):
            path_segments[i] = get_language_site_name(path_segments[i], lang)


        # ease of use variables

        result[lang] = result[lang].replace("$LANG$", lang)

        result[lang] = result[lang].replace("$PATH$", os.path.join("", *path_segments[:-1]))
        result[lang] = result[lang].replace("$PARENTPATH$", os.path.join("", *path_segments[:-2]))

        result[lang] = result[lang].replace("$PATHEND$", path_segments[-2])

        for lang2 in LANGUAGES:
            result[lang2] = result[lang2].replace(f"$PATH[{lang}]$", os.path.join("", *path_segments[:-1]))


        genloc[lang] = os.path.join(GENERATION_LOCATION, *path_segments)



    # writing generated files

    for lang in LANGUAGES:
        os.makedirs(os.path.dirname(genloc[lang]), exist_ok=True)
        with open(genloc[lang], "w") as f:
            _ = f.write(result[lang])
            print("Generated html at", genloc[lang])





# creates site and templates folder if they don't exist

if not os.path.exists(PREPROCESSED_SITE_LOCATION):
    os.mkdir(PREPROCESSED_SITE_LOCATION)

if not os.path.exists(TEMPLATE_LOCATION):
    os.mkdir(TEMPLATE_LOCATION)

if not os.path.exists(RESOURCE_LOCATION):
    os.mkdir(RESOURCE_LOCATION)



# creates empty folder for the site generation

if os.path.exists(GENERATION_LOCATION):
    shutil.rmtree(GENERATION_LOCATION)
os.mkdir(GENERATION_LOCATION)



# parses all the template files

for root, dirs, files in os.walk(TEMPLATE_LOCATION):
    for file in files:
        if file.endswith(".html"):
            _ = expand_template(os.path.join(root, file))



# generates html file for each raw html file

for root, dirs, files in os.walk(PREPROCESSED_SITE_LOCATION):
    for file in files:
        if file.endswith(".html"):
            generate_html(os.path.join(root, file))

_ = shutil.copytree(RESOURCE_LOCATION, os.path.join(GENERATION_LOCATION, os.path.basename(os.path.normpath(RESOURCE_LOCATION))))
