package main

import rego.v1

is_deploy if input.kind == "Deployment"

deny contains msg if {
  is_deploy
  input.spec.replicas < 2
  msg := "Deployment needs replicas >= 2 for zero-downtime updates"
}

deny contains msg if {
  is_deploy
  object.get(input, ["spec", "strategy", "rollingUpdate", "maxUnavailable"], 1) != 0
  msg := "rollingUpdate.maxUnavailable must be 0 (never remove a pod before its replacement is ready)"
}

deny contains msg if {
  is_deploy
  some c in input.spec.template.spec.containers
  not c.readinessProbe
  msg := sprintf("container '%s' has no readinessProbe", [c.name])
}

deny contains msg if {
  is_deploy
  some c in input.spec.template.spec.containers
  endswith(c.image, ":latest")
  msg := sprintf("container '%s' uses the :latest tag", [c.name])
}

deny contains msg if {
  is_deploy
  some c in input.spec.template.spec.containers
  not c.resources.limits
  msg := sprintf("container '%s' has no resource limits", [c.name])
}

deny contains msg if {
  is_deploy
  some c in input.spec.template.spec.containers
  not c.securityContext.runAsNonRoot
  msg := sprintf("container '%s' must set securityContext.runAsNonRoot: true", [c.name])
}
