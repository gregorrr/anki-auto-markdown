This plugin is officially retired (unless someone else picks it up) as from Anki 2.1.50+ the internals of Anki have changed and this plugin no longer functions. Anyone is free to fork and continue this plugin in any way.

---
# Auto Markdown

This is a fork of the _excellent_ markdown plugin by @gregorrr. The purpose of
this fork is to maintain bugfixes and keep up to date with changes in Anki.

There are no current plans to add new features.

## QA testing
In leiu of good automated testing for Anki plugins, the following things should be checked when preparing a release:

* Fields in the editor can be toggled with `Ctrl + m`
* Enabling auto markdown on fields can be done in Note Types (`Ctrl + Shift + n`) > press Fields button  
* Enabling auto markdown on fields can be done in Note Types (`Ctrl + Shift + n`) > press Fields button with a new card type


## Original README file.

> Source for the [Auto Markdown](https://ankiweb.net/shared/info/1030875226) Anki add-on.
> 
> ## To-do
> 
> ### Better implementation of fields.py
> 
> Current code is incompatible with other add-ons. 
> 
> ## Possible Features
> 
> ### Convert-all to Markdown button
> 
> Have convert-all-to and convert-all-from buttons to allow easier adoptation and prevent lock-in.
> 
> ### Field should be auto markdown by convention
> 
> Allow setting of custom field name suffix, e.g. "_mkd_", to indicate that the field should be auto markdown.
