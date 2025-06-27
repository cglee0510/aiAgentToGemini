from clight.system.importer import *


class SemVer:
    ####################################################################################// Load
    def __init__(self, default_tag: str = 'alpha'):
        self.test = False
        self.default_tag = default_tag
        self.semver_pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z]+)\.(\d+))?$"
        self.precedence = {"alpha": 1, "beta": 2, "rc": 3}
        pass

    ####################################################################################// Main
    def bump(current: str = "0.0.0", action: str = None):
        obj = SemVer()
        obj.test = action != None

        if not SemVer.valid(current):
            cli.error(f"Invalid current version: " + current)
            return ""

        parts = obj.__getParts(current)
        if not obj.test:
            if parts.tag:
                promote = obj.__askPromotion(parts.major, parts.minor, parts.patch, parts.tag)
                if promote:
                    return promote
            action = obj.__askChangeType()
        
        if action not in ["major", "minor", "patch"]:
            return ""

        if not obj.test and action == "major" and not parts.tag:
            stage = obj.__askStage()
            if stage:
                number = obj.__bumpNumber(action, parts.major, parts.minor, parts.patch)
                return number + stage

        if parts.tag:
            return obj.__bumpTag(action, parts.major, parts.minor, parts.patch, parts.tag, parts.tagN)

        return obj.__bumpNumber(action, parts.major, parts.minor, parts.patch)

    def umbrella(old_version: str, old_versions: List[str], new_versions: List[str]):
        obj = SemVer()
        if len(old_versions) != len(new_versions):
            cli.error("Old and new sub-version lists must match in length")
            sys.exit()

        umb_maj, umb_min, umb_pat, _, _ = obj.__parseVersion(old_version)
        highest_severity = 0
        prereleases: List[Tuple[str, int]] = []

        for ov, nv in zip(old_versions, new_versions):
            old_v = obj.__parseVersion(ov)
            new_v = obj.__parseVersion(nv)
            sev = obj.__bumpSeverity(old_v, new_v)
            highest_severity = max(highest_severity, sev)
            if new_v[3] and new_v[4] is not None:
                prereleases.append((new_v[3], new_v[4]))

        if highest_severity == 3:
            umb_maj += 1
            umb_min = 0
            umb_pat = 0
        elif highest_severity == 2:
            umb_min += 1
            umb_pat = 0
        elif highest_severity == 1:
            umb_pat += 1

        if prereleases:
            best_label = max(
                prereleases, key=lambda x: (obj.precedence.get(x[0], 0), x[1])
            )[0]
            nums = [num for lbl, num in prereleases if lbl == best_label]
            best_num = max(nums) if nums else 1
            return f"{umb_maj}.{umb_min}.{umb_pat}-{best_label}.{best_num}"

        return f"{umb_maj}.{umb_min}.{umb_pat}"

    def valid(version: str):
        semver_regex = re.compile(
            r"""
            ^                        # start of string
            (0|[1-9]\d*)             # major
            \.
            (0|[1-9]\d*)             # minor
            \.
            (0|[1-9]\d*)             # patch
            (?:-                     # optional suffix
              (?:
                (?:                  # — pre-release branch —
                  (?:alpha|beta|rc)  #   must be one of these
                  (?:\.(?:0|[1-9]\d*))*  #   optional .number segments (no leading zeros)
                )
              |
                (?:                  # — build‐metadata branch —
                  build              #   literal “build”
                  (?:\.[\da-zA-Z-]+)*   #   dot‐separated alphanumeric (leading zeros OK)
                )
              )
            )?                       # suffix is entirely optional
            $                        # end of string
            """,
            re.VERBOSE,
        )

        return bool(semver_regex.match(version))

    ####################################################################################// Tests
    def test_check():
        return SemVer.__test_check({
            "1.0.0": True,
            "2.5.1-alpha": True,
            "0.9.0-alpha.1": True,
            "0.9.0-alpha.": False,
            "0.9.0-.": False,
            "0.9.0-rc.": False,
            "0.9.0-rc.1": True,
            "0.9.0-beta.123": True,
            "102.900.223-alpha.123": True,
            "102.900.223-beta.123": True,
            "102.900.223-tota": False,
            "102.900.223-": False,
            "1.0.0-0.3.7": False,
            "1.0.0-0.3.": False,
            "1.2.3+build.001": False,
            "1.2.3-build.001": True,
            "102.900.023-alpha.123": False,
            "01.2.3": False,  
            "1.02.3": False,  
            "1.2.03": False,  
            "1.2": False,
            "1.2.": False,
            "...": False,
            "1...": False,
            "1.2.3-": False,
        })

    def test_bump():
        return SemVer.__test_bump([
            # Stable bumps
            ("1.2.1", "patch", "1.2.2"),
            ("1.2.1", "minor", "1.3.0"),
            ("1.2.1", "major", "2.0.0"),
            # More stable cases
            ("10.4.6", "patch", "10.4.7"),
            ("10.4.6", "minor", "10.5.0"),
            ("10.4.6", "major", "11.0.0"),
            # Alpha prerelease bumps
            ("6.1.0-alpha.1", "patch", "6.1.0-alpha.2"),
            ("6.1.0-alpha.1", "minor", "6.2.0-alpha.1"),
            ("6.1.0-alpha.1", "major", "7.0.0-alpha.1"),
            ("1.0.0-alpha.9", "patch", "1.0.0-alpha.10"),
            ("1.0.0-alpha.9", "minor", "1.1.0-alpha.1"),
            # Beta prerelease bumps
            ("6.1.0-beta.1", "patch", "6.1.0-beta.2"),
            ("6.1.0-beta.1", "minor", "6.2.0-alpha.1"),
            ("6.1.0-beta.1", "major", "7.0.0-alpha.1"),
            ("2.0.0-beta.9", "patch", "2.0.0-beta.10"),
            ("2.0.0-beta.9", "minor", "2.1.0-alpha.1"),
            ("2.0.0-beta.9", "major", "3.0.0-alpha.1"),
            # RC prerelease bumps
            ("6.1.0-rc.1", "patch", "6.1.0-rc.2"),
            ("6.1.0-rc.1", "minor", "6.2.0-alpha.1"),
            ("6.1.0-rc.1", "major", "7.0.0-alpha.1"),
            ("1.0.0-rc.9", "patch", "1.0.0-rc.10"),
            ("1.0.0-rc.9", "minor", "1.1.0-alpha.1"),
            ("1.0.0-rc.9", "major", "2.0.0-alpha.1"),
            # Edge cases: zero versions
            ("0.0.0", "patch", "0.0.1"),
            ("0.0.0", "minor", "0.1.0"),
            ("0.0.0", "major", "1.0.0"),
            # Error handling tests
            ("1.2.3", "inval", "Invalid bump type 'inval'. Use 'patch', 'minor', or 'major'."),
            ("1.2", "patch", "Invalid version string: '1.2'"),
            ("1.2.3.4", "patch", "Invalid version string: '1.2.3.4'"),
        ])

    def test_umbrella():
        return SemVer.__test_umbrella([
            # 1. Pure patch bumps -> patch bump
            (
                "2.3.4",
                ["1.0.0", "2.3.4", "4.0.1"],
                ["1.0.1", "2.3.5", "4.0.2"],
                "2.3.5"
            ),
            # 2. Mixed patches + one minor -> minor bump
            (
                "2.3.4",
                ["1.0.0", "2.3.4", "4.0.1"],
                ["1.0.1", "2.4.0", "4.0.2"],
                "2.4.0"
            ),
            # 3. Major bump in any repo -> major bump
            (
                "2.3.4",
                ["1.0.0", "2.3.4", "4.0.1"],
                ["1.0.0", "3.0.0", "4.0.1"],
                "3.0.0"
            ),
            # 4. No changes -> no bump
            (
                "1.2.3",
                ["1.0.0", "2.1.1", "3.4.5"],
                ["1.0.0", "2.1.1", "3.4.5"],
                "1.2.3"
            ),
            # 5. Pre-release bump only -> patch bump + label
            (
                "0.1.0-alpha.1",
                ["0.1.0-alpha.1", "1.0.0", "2.0.0"],
                ["0.1.0-alpha.2", "1.0.0", "2.0.0"],
                "0.1.1-alpha.2"
            ),
            # 6. Pre-release selection across labels
            (
                "2.3.4-beta.1",
                ["1.0.0-alpha.2", "2.3.4", "4.0.1-rc.1"],
                ["1.0.1", "2.4.0-beta.2", "4.0.1-rc.1"],
                "2.3.5-rc.1"
            ),
            # 7. Pre-release removal -> patch bump
            (
                "3.0.0-beta.3",
                ["1.0.0-beta.3", "2.0.0-alpha.2", "3.0.0-alpha.1"],
                ["1.0.0", "2.0.0-alpha.2", "3.0.0-alpha.1"],
                "3.0.1-alpha.2"
            ),
            # 8. Mixed removal and bump -> patch bump and select label
            (
                "3.0.1-alpha.2",
                ["1.0.0", "2.0.0-alpha.2", "3.0.0-alpha.1"],
                ["1.0.0", "2.0.0", "3.0.0-alpha.1"],
                "3.0.2-alpha.1"
            ),
            # 9. All subs stable -> stable patch bump
            (
                "3.0.2-alpha.1",
                ["1.0.0", "2.0.0", "3.0.0-alpha.1"],
                ["1.0.0", "2.0.0", "3.0.0"],
                "3.0.3"
            ),
            # 10. Pre-release upgrades in all -> bump with highest label
            (
                "1.0.0-alpha.1",
                ["1.0.0-alpha.1", "2.0.0-alpha.1", "3.0.0-alpha.1"],
                ["1.0.0-beta.1", "2.0.0-beta.1", "3.0.0-beta.1"],
                "1.0.1-beta.1"
            ),
            # 11. Mixed stable and beta to full release
            (
                "4.5.6-beta.2",
                ["1.0.0-beta.2", "2.0.0-beta.2", "3.0.0"],
                ["1.0.0", "2.0.0", "3.0.0"],
                "4.5.7"
            ),
            # 12. Jump from patch to major in two repos
            (
                "1.1.1",
                ["0.1.0", "1.1.1", "1.0.0"],
                ["1.0.0", "2.0.0", "2.0.0"],
                "2.0.0"
            ),
            # 13. Beta to rc in multiple -> highest label preserved
            (
                "0.9.9-beta.1",
                ["1.0.0-beta.1", "2.0.0-beta.1"],
                ["1.0.0-rc.1", "2.0.0-rc.1"],
                "0.9.10-rc.1"
            ),
            # 14. Stable to alpha in one repo -> label attached
            (
                "1.0.0",
                ["1.0.0", "2.0.0"],
                ["1.0.0", "2.0.0-alpha.1"],
                "1.0.1-alpha.1"
            ),
            # 15. RC to final release in one -> label removed
            (
                "1.2.3-rc.2",
                ["1.0.0-rc.2", "2.0.0"],
                ["1.0.0", "2.0.0"],
                "1.2.4"
            ),
            # 16. Alpha increased in one -> label and patch bumped
            (
                "1.2.4-alpha.1",
                ["1.0.0-alpha.1", "2.0.0"],
                ["1.0.0-alpha.2", "2.0.0"],
                "1.2.5-alpha.2"
            ),
            # 17. RC to stable in all -> final release
            (
                "2.3.9-rc.3",
                ["1.0.0-rc.3", "2.0.0-rc.3"],
                ["1.0.0", "2.0.0"],
                "2.3.10"
            ),
            # 18. Alpha and beta upgraded -> beta takes priority
            (
                "0.1.0-alpha.3",
                ["1.0.0-alpha.3", "2.0.0"],
                ["1.0.0-beta.1", "2.0.0"],
                "0.1.1-beta.1"
            ),
            # 19. Downgrade from beta to alpha -> still bumps patch with alpha label
            (
                "0.1.1-beta.1",
                ["1.0.0-beta.1", "2.0.0"],
                ["1.0.0-alpha.1", "2.0.0"],
                "0.1.2-alpha.1"
            ),
            # 20. Mixed patch + label introduction
            (
                "1.2.3",
                ["1.0.0", "2.0.0"],
                ["1.0.1", "2.0.0-alpha.1"],
                "1.2.4-alpha.1"
            ),
        ])

    ####################################################################################// Helpers
    
    def __parseVersion(self, version: str) -> Tuple[int, int, int, Optional[str], Optional[int]]:
        match = re.match(self.semver_pattern, version)
        if not match:
            cli.error(f"Invalid version format: '{version}'. Expected 'MAJOR.MINOR.PATCH[-label.number]'.")
            sys.exit()

        major, minor, patch = map(int, match.groups()[:3])
        label = match.group(4)
        label_num = int(match.group(5)) if match.group(5) else None

        return major, minor, patch, label, label_num

    def __bumpSeverity(self, old: Tuple[int, int, int, Optional[str], Optional[int]], new: Tuple[int, int, int, Optional[str], Optional[int]]):
        old_maj, old_min, old_pat, old_lbl, old_num = old
        new_maj, new_min, new_pat, new_lbl, new_num = new

        # Pre-release removal (old had label, new is stable) -> patch
        if old_lbl is not None and new_lbl is None:
            return 1

        # Any pre-release bump (new label or label number increase) -> patch
        if new_lbl is not None and (
            new_lbl != old_lbl
            or (
                old_lbl == new_lbl
                and old_num is not None
                and new_num is not None
                and new_num > old_num
            )
        ):
            return 1

        # Stable major bump
        if new_lbl is None and new_maj > old_maj:
            return 3
        # Stable minor bump
        if new_lbl is None and new_min > old_min:
            return 2
        # Stable patch bump
        if new_lbl is None and new_pat > old_pat:
            return 1

        return 0

    def __getParts(self, current: str):
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z]+)\.(\d+))?$'
        match = re.match(pattern, current)

        parts = types.SimpleNamespace()
        parts.major, parts.minor, parts.patch = map(int, match.groups()[:3])
        parts.tag = match.group(4)
        parts.tagN = int(match.group(5)) if match.group(5) else None

        return parts

    def __askPromotion(self, major: int, minor: int, patch: int, tag: int):
        new = self.__askStagePromotion(tag)
        if new != tag:
            if not new:
                return f"{major}.{minor}.{patch}"
            return f"{major}.{minor}.{patch}-{new}.1"
        return ""

    def __bumpTag(self, action: str, major: int, minor: int, patch: int, tag: int, tagN: int):
        if action == "patch":
            new_pr_num = tagN + 1
            return f"{major}.{minor}.{patch}-{tag}.{new_pr_num}"

        if action == "minor":
            minor += 1
            patch = 0
        else:  # major
            major += 1
            minor = 0
            patch = 0

        return f"{major}.{minor}.{patch}-{self.default_tag}.1"

    def __bumpNumber(self, action: str, major: int, minor: int, patch: int):
        if action == "patch":
            patch += 1
        elif action == "minor":
            minor += 1
            patch = 0
        else:  # major bump
            major += 1
            minor = 0
            patch = 0

        return f"{major}.{minor}.{patch}"

    def __askStagePromotion(self, tag: str):
        if self.test:
            return tag
        elif tag == "alpha" and cli.confirmation('Is it ready to be promoted to "beta" stage?'):
            return "beta"
        elif tag == "beta" and cli.confirmation('Is it ready to be promoted to "rc" stage as release candidate?'):
            return "rc"
        elif tag == "rc" and cli.confirmation('Is it ready to be released as "stable" version?'):
            return ""
        else:
            return tag

    def __askStage(self):
        options = {
            "Stable - Good to go live!": "",
            "Alpha - Still building things out": "-alpha.1",
            "Beta - All there, but testing needed": "-beta.1",
            "RC - Just about done, final checks": "-rc.1",
        }

        selected = cli.selection("What stage are you moving to?", list(options.keys()), True)

        return options[selected]

    def __askChangeType(self):
        options = {
            "Patch - Everything works the same, but bugs were fixed or small internal improvements made": "patch",
            "Minor - Everything still works, plus they get new features or enhancements": "minor",
            "Major - Their existing code might break, or behavior has changed in an incompatible way": "major",
        }

        selected = cli.selection("What will your users or clients experience with this change?", list(options.keys()), True)

        return options[selected]

    def __test_check(cases: dict ={}):
        cli.info(f"Must  | Got   | Case")
        cli.info("--------------------------------------------")
        for case in cases:
            expect = cases[case]
            result = SemVer.valid(case)
            if cases[case] == result:
                cli.done(f"{str(expect):5s} | {str(result):6s}| {case}")
                continue
            print(f"{str(expect):5s} | {str(result):6s}| {case}")
        cli.info("--------------------------------------------\n")
        sys.exit()

    def __test_bump(cases: list =[]):
        cli.info(f"Case  | Current       | New")
        cli.info("--------------------------------------------")
        for version, action, expected in cases:
            result = SemVer.bump(version, action)
            if result == expected:
                cli.done(f"{action:6s}| {str(version):13s} | {str(result):6s}")
            else:
                print(f"{action:6s}| {str(version):13s} | {str(result):6s}")
        cli.info("--------------------------------------------\n")
        sys.exit()

    def __test_umbrella(cases: list =[]):
        cli.info(f"Old Version   | New Version")
        cli.info("--------------------------------------------")
        for old_uv, old_versions, new_versions, umbrella in cases:
            result = SemVer.umbrella(old_uv, old_versions, new_versions)
            if result == umbrella:
                cli.done(f'{old_uv:13s} | {result}')
            else:
                print(f'Returned umbrella version: "{result}" when expecting "{umbrella}"')
        cli.info("--------------------------------------------\n")
        sys.exit()
