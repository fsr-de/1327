from django import template
from guardian.templatetags.guardian_tags import get_obj_perms as guardian_obj_perms, ObjectPermissionsNode as GuardianObjectPermissionChecker

register = template.Library()


class ObjectPermissionsNode(GuardianObjectPermissionChecker):

	def __init__(self, for_whom, obj, context_var):
		super(ObjectPermissionsNode, self).__init__(str(for_whom), str(obj), str(context_var))

	def render(self, context):
		super(ObjectPermissionsNode, self).render(context)
		context[self.context_var] = list(map(lambda x: x.split('_')[0], context[self.context_var]))
		return ""


@register.tag
def get_obj_perms(parser, token):
	"""
		change standard django guardian behaviour when it comes to get permission names for user
		standard behaviour: return codenames like "permission_applabel"
		new behaviour: return codenames like "permission"
	"""
	guardian_permission_node = guardian_obj_perms(parser, token)
	return ObjectPermissionsNode(guardian_permission_node.for_whom, guardian_permission_node.obj, guardian_permission_node.context_var)
