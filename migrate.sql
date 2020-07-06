UPDATE
   reversion_version
SET
	serialized_data = REPLACE (
		serialized_data,
		'"url_title":',
		'"title_en": "", "url_title":'
   )
WHERE serialized_data LIKE '%"title":%';

UPDATE
   reversion_version
SET
   serialized_data = REPLACE (
		serialized_data,
		'"hash_value":',
		'"text_en": "", "hash_value":'
   )
WHERE serialized_data LIKE '%"title":%';

UPDATE
   reversion_version
SET
   serialized_data = REPLACE (
		serialized_data,
		'"title":',
		'"title_de":'
   );

UPDATE
   reversion_version
SET
   serialized_data = REPLACE (
		serialized_data,
		'"text":',
		'"text_de":'
   );
