*** Settings ***
Documentation     Test the xls-to-pdf-ical website
Library           SeleniumLibrary
Library           OperatingSystem
Library           ArchiveLibrary
Library           lib/CreateProfile.py

*** Variables ***
${URL}            http://calendar.acaird.com
${DLDIR}          ${CURDIR}/downloads
${DLBUTTON}       Create Zip file of PDF and ICS files
${BROWSER}        Headless Firefox
*** Test Cases ***
Page Loads
	${profile}         Create Firefox Profile   ${DLDIR}
	Log                ${profile}
	Open Browser       ${URL}    ${BROWSER}   ff_profile_dir=${profile}
	Title Should Be    Excel to Calendars
Upload File
	Choose File        id:inp     ${CURDIR}/sample.csv
Download File
	Create Directory             ${DLDIR}
	Empty Directory	             ${DLDIR}
	Directory Should Be Empty    ${DLDIR}
	Click Button                 ${DLBUTTON}

Close Browser
	Close Browser

Unzip Downloaded File
	extract_zip_file    ${DLDIR}/cals-sample.zip  ${DLDIR}

*** Keywords ***
