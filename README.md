# Site Generator

This is a simple site generator I wrote for [my website](https://antonipostola.xyz).
It provides template and language seperation features that extend basic html.

## Usage

The website should be written within the `PREPROCESSED_LOCATION`, which defaults to `./site/`, where you can use the features of the generator.

Any templates you may wish to use should be in the `TEMPLATE_LOCATION` which defaults to `./templates`.

For global resources you should use the `RESOURCE_LOCATION` which defaults to `./resource` as it is copied over to the generated site.

To generate the site, you run the **`generate.py`** file. This will generate the new site to the `GENERATION_LOCATION`, which is `./generated_site` by default.

## Features

### LanguageSite Attribute
The main feature of the generator are the language features. For any given HTML tag, you can specify a `LanguageSite` attribute to decide which language site the tag will appear in. The language of the tag is inherited but if it and the parents have no language specified, the tag will be added to all the sites. Here is an example usage:
```
<div>
    <p LanguageSite="en"> 
        Hello <span>human</span>
    </p>
    <p LanguageSite="fr"> 
        Salut <span>humain</span>
    </p>
</div>
```
Here, the \<div\> tag will be added to both the English and French sites, while the \<p\> tags and their children will go to their respective language sites.

### Path variables
There are path variables you can use to decrease the need for manually entering cross-language URLs and similar. Any occurence of them will be replaced with their value. They are listed below:
- `$LANG$` - Replaced with the language identifier of the generated site.
- `$PATH$` - Replaced with the full (website-local) path of the generated site.
- `$PATH[<language identifier>]$` - Replaced with the full (website-local) path of the generated site for the specified language.
- `$PARENTPATH$` - Replaced with the full (website-local) path of the parent site.
- `$PATHEND$` - Replaced with the end of the site path - if the site was at foo/bar/foobar, foobar would be returned.

### Templates
Templates are defined by html files in the `TEMPLATE_LOCATION` folder. They reduce the need for retyping similar information.
#### Definition
Templates are mostly just html that will be copied in when the template tag is used. However, when defining the template there are 3 special tags that can be used:
- The `<CustomTemplateBody/>` is used to specify where in the template the tag's contents should be put.
- The `<CustomTemplateVar/>` is used to put the string value of an attribute somewhere within the template. It is required that a 'name' attribute is also given so that we know which passed attribute to use.
- The `<VarTitle/>` is used to put the contents of a template variable inside a title. This is needed because title tags interpret strings. You use the 'name' attribute to select the variable.
#### Usage
To use a template, you use the `<CustomTemplate>` tag. You have to specify which template from the `TEMPLATE_LOCATION` to use with the `location` attribute. Any other attributes passed can be used as a `<CustomTemplateVar/>` within the template.
#### Example
If we had a template 'foo.html' like this:
```
<p>I'm from a template, I was told to say <CustomTemplateVar name="bar"/>.</p>
<CustomTemplateBody/>
<p>I'm also from a template</p>
```
And and index.html like this:
```
<CustomTemplate location="foo.html" bar="hello">
    <p>I'm a child of the template tag.</p>
<CustomTemplate/>
```
The result would be:
```
<p>I'm from a template, I was told to say hello.</p>
<p>I'm a child of the template tag.</p>
<p>I'm also from a template</p>
```

## Configuration

You can edit the target directories near the top of the python script. The variables that change them are: 
- `PREPROCESSED_LOCATION` - This is the location of the site you want to run the script on to generate the site.
- `TEMPLATE_LOCATION` - This is where all the templates are stored.
- `RESOURCE_LOCATION` - This is where all global resources are stored.
- `GENERATION_LOCATION` - This is where the site will generate to.

To change the language sites that are generated, edit the `LANGUAGES` list.

The site generator is made with the idea that one html file is responsible for all the languages of the page, so there is also a dictionary called `LANGUAGE_SITE_NAMES`. The dictionary is there to allow the same structure for the different languages, while still keeping native words in the url. The formatting goes as so:
```
LANGUAGE_SITE_NAMES {
    "<The base site name, (what it is called in the PREPROCESSED_LOCATION)>": {
        "<lang>": "<name for that language>",
    },
}
```
