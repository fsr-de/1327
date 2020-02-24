{% load i18n %}

if (documentInfo.hasOwnProperty("children") || !documentInfo.hasOwnProperty("text_de") || !documentInfo.hasOwnProperty("text_en")) {
	return documentInfo.text;
}

return $(`<span> ${documentInfo.text_de} | ${documentInfo.text_en}</span>`);
