#!/bin/bash
objdump -d $1 | grep --color -E '(vrcp14|vrsqrt14|vrcp28|vrsqrt28|vexp2|vperm|vpermi2|vgetexp|vgetmant|vscalef|vrndscale|vreduce|vfpclass|vfixupimm|vrange)'
