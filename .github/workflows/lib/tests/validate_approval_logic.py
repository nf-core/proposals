#!/usr/bin/env python3

import sys
import math


class MockApprovalManager:
    """Mock approval manager for validation testing"""
    def __init__(self):
        self.core_team_members = []
        self.core_approvals = set()
        self.maintainer_approvals = set()


def validate_pipeline_approval_logic():
    """Validate pipeline approval logic"""
    manager = MockApprovalManager()

    # Test pipeline approval with 2 core members
    manager.core_approvals = {'core1', 'core2'}
    manager.maintainer_approvals = set()
    pipeline_2_core = (len(manager.core_approvals) >= 2) or (
        len(manager.core_approvals) >= 1 and len(manager.maintainer_approvals) >= 1
    )
    print('Pipeline 2 core approval:', pipeline_2_core)

    # Test pipeline approval with 1 core + 1 maintainer
    manager.core_approvals = {'core1'}
    manager.maintainer_approvals = {'maintainer1'}
    pipeline_1_core_1_maintainer = (len(manager.core_approvals) >= 2) or (
        len(manager.core_approvals) >= 1 and len(manager.maintainer_approvals) >= 1
    )
    print('Pipeline 1 core + 1 maintainer approval:', pipeline_1_core_1_maintainer)

    if not pipeline_2_core or not pipeline_1_core_1_maintainer:
        print('Pipeline approval logic validation failed!')
        return False

    print('Pipeline approval logic validation passed!')
    return True


def validate_rfc_approval_logic():
    """Validate RFC approval logic"""
    manager = MockApprovalManager()

    # Test RFC quorum logic
    manager.core_team_members = ['core1', 'core2', 'core3', 'core4', 'core5']
    quorum = math.ceil(len(manager.core_team_members) / 2)

    manager.core_approvals = {'core1', 'core2', 'core3'}
    rfc_approved = len(manager.core_approvals) >= quorum
    print(f'RFC quorum approval (3/5): {rfc_approved}, quorum needed: {quorum}')

    manager.core_approvals = {'core1', 'core2'}
    rfc_not_approved = len(manager.core_approvals) >= quorum
    print(f'RFC insufficient approval (2/5): {rfc_not_approved}')

    if not rfc_approved or rfc_not_approved:
        print('RFC approval logic validation failed!')
        return False

    print('RFC approval logic validation passed!')
    return True


def main():
    print("Validating approval logic...")

    pipeline_valid = validate_pipeline_approval_logic()
    rfc_valid = validate_rfc_approval_logic()

    if pipeline_valid and rfc_valid:
        print("All approval logic validation passed!")
        sys.exit(0)
    else:
        print("Approval logic validation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
