{% load i18n %}

if (documentInfo.hasOwnProperty("children") || !documentInfo.hasOwnProperty("text_de") || !documentInfo.hasOwnProperty("text_en")) {
	return documentInfo.text;
}

return $(`<span><em>{% trans "German" %}:</em> ${documentInfo.text_de}<br> <em>{% trans "English" %}:</em> ${documentInfo.text_en}</span>`);
