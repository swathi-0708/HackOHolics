"""Skill ontology: canonical skills, surface aliases, and implication edges.

Three relations matter for ranking:

``aliases``   different spellings of the *same* skill ("aws" == "amazon web services").
``implies``   directed evidence: using Express is strong evidence of Node.js and
              JavaScript, even if the resume never writes those words. This is what
              lets a candidate who "built REST APIs with Express and MongoDB" score
              against a Node.js backend requirement.
``related``   same neighbourhood, weaker evidence, symmetric (Vue <-> React: both
              component-based SPA frameworks, transferable but not equivalent).

Credit flows: an exact/alias hit scores 1.0, an implied hit ``IMPLIED_CREDIT``, a
related hit ``RELATED_CREDIT``. So named tools still dominate -- loosely related
experience alone cannot fully satisfy an explicit requirement.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .normalize import normalize

IMPLIED_CREDIT = 0.75
RELATED_CREDIT = 0.45

# ---------------------------------------------------------------------------
# category, aliases, implies, related
# ---------------------------------------------------------------------------
_ONTOLOGY: dict[str, dict] = {
    # ---- languages ----
    "javascript": {
        "category": "language",
        "aliases": ["js", "ecmascript", "es6", "es2015", "vanilla js", "javscript"],
        "related": ["typescript"],
    },
    "typescript": {"category": "language", "aliases": ["ts"], "implies": ["javascript"]},
    "python": {"category": "language", "aliases": ["py", "python3", "pyhton"]},
    "java": {"category": "language", "aliases": ["java se", "core java", "java 8", "java 11"]},
    "cpp": {"category": "language", "aliases": ["c plus plus", "cpp"]},
    "c": {"category": "language", "aliases": ["c language", "ansi c"]},
    "csharp": {"category": "language", "aliases": ["csharp"], "related": ["dotnet"]},
    "php": {"category": "language", "aliases": ["php7", "php8"]},
    "ruby": {"category": "language", "aliases": []},
    "go": {"category": "language", "aliases": ["golang"]},
    "rust": {"category": "language", "aliases": []},
    "kotlin": {"category": "language", "aliases": [], "implies": ["java"]},
    "swift": {"category": "language", "aliases": []},
    "dart": {"category": "language", "aliases": []},
    "r": {"category": "language", "aliases": ["r language"]},
    "matlab": {"category": "language", "aliases": []},
    "bash": {"category": "language", "aliases": ["shell scripting", "shell", "zsh"]},

    # ---- web fundamentals ----
    "html": {"category": "frontend", "aliases": ["html5", "hypertext markup language"]},
    "css": {"category": "frontend", "aliases": ["css3", "cascading style sheets"]},
    "responsive design": {
        "category": "frontend",
        "aliases": ["responsive web design", "mobile first design", "media queries"],
        "implies": ["css"],
    },
    "sass": {"category": "frontend", "aliases": ["scss", "less"], "implies": ["css"]},
    "tailwind": {"category": "frontend", "aliases": ["tailwind css", "tailwindcss"], "implies": ["css"]},
    "bootstrap": {"category": "frontend", "aliases": ["bootstrap 5"], "implies": ["css"]},
    "material ui": {"category": "frontend", "aliases": ["mui", "material design"], "implies": ["css"]},
    "jquery": {"category": "frontend", "aliases": [], "implies": ["javascript"]},

    # ---- frontend frameworks ----
    "react": {
        "category": "frontend",
        "aliases": ["reactjs", "react hooks", "react native"],
        "implies": ["javascript"],
        "related": ["vue", "angular", "svelte"],
    },
    "redux": {"category": "frontend", "aliases": ["redux toolkit", "zustand"], "implies": ["react", "javascript"]},
    "nextjs": {
        "category": "frontend",
        "aliases": ["nextjs"],
        "implies": ["react", "javascript", "nodejs", "server side rendering"],
    },
    "vue": {"category": "frontend", "aliases": ["vuejs", "vue 3", "nuxtjs"], "implies": ["javascript"],
            "related": ["react", "angular"]},
    "angular": {"category": "frontend", "aliases": ["angularjs", "angular 2"], "implies": ["typescript", "javascript"],
                "related": ["react", "vue"]},
    "svelte": {"category": "frontend", "aliases": ["sveltekit"], "implies": ["javascript"], "related": ["react"]},
    "server side rendering": {"category": "frontend", "aliases": ["ssr", "static site generation", "ssg"]},

    # ---- backend / API ----
    "nodejs": {
        "category": "backend",
        "aliases": ["nodejs", "node", "node runtime", "server side javascript"],
        "implies": ["javascript", "backend development"],
        "related": ["deno", "bun"],
    },
    "expressjs": {
        "category": "backend",
        "aliases": ["expressjs", "express", "express framework", "expres"],
        "implies": ["nodejs", "javascript", "rest api", "backend development"],
        "related": ["nestjs", "fastify", "koa"],
    },
    "nestjs": {"category": "backend", "aliases": ["nestjs"], "implies": ["nodejs", "typescript", "rest api"]},
    "fastify": {"category": "backend", "aliases": ["koa", "hapi"], "implies": ["nodejs", "rest api"]},
    "deno": {"category": "backend", "aliases": ["bun"], "implies": ["javascript"]},
    "rest api": {
        "category": "backend",
        "aliases": ["rest", "rest api", "restful api", "rest apis", "web api", "http api",
                    "api development", "api design", "json api", "crud api", "api endpoint",
                    "api integration"],
        "implies": ["backend development"],
        "related": ["graphql", "grpc", "soap"],
    },
    "graphql": {"category": "backend", "aliases": ["apollo", "apollo server"], "implies": ["rest api"],
                "related": ["rest api"]},
    "grpc": {"category": "backend", "aliases": ["protobuf", "protocol buffers"], "related": ["rest api"]},
    "soap": {"category": "backend", "aliases": ["xml web services"], "related": ["rest api"]},
    "backend development": {
        "category": "backend",
        "aliases": ["backend", "server side development", "server side", "microservice",
                    "microservices", "server development"],
    },
    "authentication": {
        "category": "backend",
        "aliases": ["jwt", "json web token", "oauth", "oauth2", "auth flow", "authorization",
                    "session management", "passport js", "role based access control", "rbac"],
    },
    "websockets": {"category": "backend", "aliases": ["socketio", "web socket", "real time messaging"]},
    "django": {"category": "backend", "aliases": ["django rest framework", "drf"],
               "implies": ["python", "rest api", "backend development"], "related": ["flask", "fastapi"]},
    "flask": {"category": "backend", "aliases": [], "implies": ["python", "rest api", "backend development"],
              "related": ["django", "fastapi"]},
    "fastapi": {"category": "backend", "aliases": [], "implies": ["python", "rest api", "backend development"],
                "related": ["flask", "django"]},
    "spring boot": {"category": "backend", "aliases": ["spring", "spring mvc", "hibernate"],
                    "implies": ["java", "rest api", "backend development"]},
    "dotnet": {"category": "backend", "aliases": ["dotnet", "asp net", "asp dotnet", "dotnet core"],
               "implies": ["csharp", "backend development"]},
    "laravel": {"category": "backend", "aliases": ["codeigniter"], "implies": ["php", "backend development"]},
    "rails": {"category": "backend", "aliases": ["ruby on rails"], "implies": ["ruby", "backend development"]},

    # ---- data stores ----
    "sql": {
        "category": "database",
        "aliases": ["structured query language", "sql queries", "joins", "relational database",
                    "rdbms", "stored procedure", "database normalization"],
    },
    "mysql": {"category": "database", "aliases": ["mariadb"], "implies": ["sql"]},
    "postgresql": {"category": "database", "aliases": ["postgres", "psql", "postgre sql"], "implies": ["sql"]},
    "sqlite": {"category": "database", "aliases": [], "implies": ["sql"]},
    "sql server": {"category": "database", "aliases": ["ms sql", "mssql", "t sql"], "implies": ["sql"]},
    "oracle db": {"category": "database", "aliases": ["oracle database", "pl sql"], "implies": ["sql"]},
    "mongodb": {"category": "database", "aliases": ["mongo", "mongo db", "mongod", "nosql", "document database"],
                "related": ["postgresql", "firebase"]},
    "mongoose": {"category": "database", "aliases": ["mongoose odm"], "implies": ["mongodb", "nodejs"]},
    "prisma": {"category": "database", "aliases": ["sequelize", "typeorm", "orm", "knex"],
               "implies": ["sql", "nodejs"]},
    "redis": {"category": "database", "aliases": ["memcached", "in memory cache"], "related": ["mongodb"]},
    "firebase": {"category": "database", "aliases": ["firestore", "realtime database", "supabase"],
                 "related": ["mongodb"]},
    "elasticsearch": {"category": "database", "aliases": ["opensearch", "lucene"]},

    # ---- tooling / delivery ----
    "git": {"category": "tooling", "aliases": ["git version control", "gitflow", "version control",
                                               "source control", "branching strategy"]},
    "github": {"category": "tooling", "aliases": ["gitlab", "bitbucket", "pull request", "code review"],
               "implies": ["git"]},
    "docker": {"category": "devops", "aliases": ["containerization", "containers", "dockerfile", "docker compose"]},
    "kubernetes": {"category": "devops", "aliases": ["k8s", "helm"], "implies": ["docker"]},
    "cicd": {"category": "devops", "aliases": ["cicd", "continuous integration", "continuous deployment",
                                               "continuous delivery", "github actions", "jenkins",
                                               "gitlab ci", "circleci", "build pipeline", "deployment pipeline"]},
    "aws": {"category": "cloud", "aliases": ["amazon web services", "ec2", "s3", "lambda", "cloudfront",
                                             "elastic beanstalk", "amazon s3"], "implies": ["cloud"]},
    "azure": {"category": "cloud", "aliases": ["microsoft azure", "azure devops"], "implies": ["cloud"],
              "related": ["aws"]},
    "gcp": {"category": "cloud", "aliases": ["google cloud", "google cloud platform", "app engine",
                                             "cloud run"], "implies": ["cloud"], "related": ["aws"]},
    "cloud": {"category": "cloud", "aliases": ["cloud deployment", "cloud hosting", "cloud infrastructure",
                                               "heroku", "netlify", "vercel", "render", "digitalocean"]},
    "linux": {"category": "devops", "aliases": ["ubuntu", "unix", "debian", "centos"]},
    "nginx": {"category": "devops", "aliases": ["apache", "reverse proxy", "load balancer"]},
    "terraform": {"category": "devops", "aliases": ["infrastructure as code", "iac", "ansible", "pulumi"]},
    "webpack": {"category": "tooling", "aliases": ["vite", "babel", "rollup", "esbuild", "parcel"],
                "implies": ["javascript"]},
    "npm": {"category": "tooling", "aliases": ["yarn", "pnpm", "package manager"], "implies": ["nodejs"]},
    "postman": {"category": "tooling", "aliases": ["insomnia", "swagger", "openapi", "api documentation"],
                "implies": ["rest api"]},
    "jira": {"category": "tooling", "aliases": ["confluence", "trello", "asana", "linear"]},
    "figma": {"category": "tooling", "aliases": ["adobe xd", "sketch", "wireframe", "wireframing", "ui mockup"]},

    # ---- quality ----
    "testing": {
        "category": "quality",
        "aliases": ["unit testing", "unit test", "integration testing", "test automation",
                    "automated testing", "test coverage", "tdd", "test driven development",
                    "end to end testing", "e2e testing", "regression testing"],
    },
    "jest": {"category": "quality", "aliases": ["mocha", "chai", "vitest", "jasmine"],
             "implies": ["testing", "javascript"]},
    "pytest": {"category": "quality", "aliases": ["unittest"], "implies": ["testing", "python"]},
    "junit": {"category": "quality", "aliases": ["mockito", "testng"], "implies": ["testing", "java"]},
    "cypress": {"category": "quality", "aliases": ["playwright", "selenium", "puppeteer"], "implies": ["testing"]},
    "debugging": {"category": "quality", "aliases": ["troubleshooting", "root cause analysis",
                                                     "bug fixing", "profiling"]},

    # ---- cs fundamentals ----
    "data structures": {"category": "fundamentals", "aliases": ["dsa", "data structure", "algorithms",
                                                                "algorithm design", "problem solving",
                                                                "competitive programming", "leetcode",
                                                                "time complexity"]},
    "oop": {"category": "fundamentals", "aliases": ["object oriented programming", "object oriented design",
                                                    "oops", "solid principles", "design pattern"]},
    "operating systems": {"category": "fundamentals", "aliases": ["os concepts", "concurrency",
                                                                  "multithreading", "process scheduling"]},
    "computer networks": {"category": "fundamentals", "aliases": ["networking", "tcp ip", "http protocol",
                                                                  "dns", "osi model"]},
    "system design": {"category": "fundamentals", "aliases": ["scalability", "distributed systems",
                                                              "architecture design", "high availability",
                                                              "caching strategy"]},

    # ---- data / ML (present in weak-fit resumes; keeps them scored, not crashed) ----
    "machine learning": {"category": "data", "aliases": ["ml", "deep learning", "neural network",
                                                         "model training", "supervised learning"],
                         "implies": ["python"]},
    "pandas": {"category": "data", "aliases": ["numpy", "scipy", "dataframe"], "implies": ["python"]},
    "tensorflow": {"category": "data", "aliases": ["pytorch", "keras", "scikit learn", "sklearn"],
                   "implies": ["machine learning", "python"]},
    "nlp": {"category": "data", "aliases": ["natural language processing", "text classification",
                                            "sentiment analysis", "transformers", "bert"],
            "implies": ["machine learning"]},
    "computer vision": {"category": "data", "aliases": ["opencv", "image classification",
                                                        "object detection"], "implies": ["machine learning"]},
    "data analysis": {"category": "data", "aliases": ["data analytics", "eda", "exploratory data analysis",
                                                      "data visualization", "dashboarding"]},
    "power bi": {"category": "data", "aliases": ["tableau", "looker", "metabase"], "implies": ["data analysis"]},
    "excel": {"category": "data", "aliases": ["ms excel", "spreadsheet", "pivot table", "vlookup",
                                              "google sheets"]},
    "etl": {"category": "data", "aliases": ["data pipeline", "airflow", "data warehouse", "spark",
                                            "hadoop", "kafka"]},

    # ---- mobile ----
    "android": {"category": "mobile", "aliases": ["android studio", "android sdk", "jetpack compose"],
                "implies": ["java"]},
    "ios": {"category": "mobile", "aliases": ["xcode", "swiftui"], "implies": ["swift"]},
    "flutter": {"category": "mobile", "aliases": [], "implies": ["dart"], "related": ["react"]},

    # ---- other domains (weak-fit resumes) ----
    "cybersecurity": {"category": "security", "aliases": ["penetration testing", "pentest", "vapt",
                                                          "vulnerability assessment", "owasp", "burp suite",
                                                          "ethical hacking", "security audit"]},
    "networking hardware": {"category": "other", "aliases": ["cisco", "ccna", "router configuration",
                                                             "switch configuration", "vlan"]},
    "embedded systems": {"category": "other", "aliases": ["arduino", "raspberry pi", "microcontroller",
                                                          "iot", "verilog", "vhdl", "plc"]},
    "mechanical cad": {"category": "other", "aliases": ["autocad", "solidworks", "catia", "ansys",
                                                        "cad modeling", "thermodynamics"]},
    "civil engineering": {"category": "other", "aliases": ["staad pro", "revit", "structural analysis",
                                                           "surveying", "concrete design"]},
    "digital marketing": {"category": "other", "aliases": ["seo", "sem", "social media marketing",
                                                           "content marketing", "google analytics",
                                                           "email campaign"]},
    "graphic design": {"category": "other", "aliases": ["photoshop", "illustrator", "canva",
                                                        "coreldraw", "branding"]},
    "content writing": {"category": "other", "aliases": ["copywriting", "blog writing", "technical writing",
                                                         "editing"]},
    "accounting": {"category": "other", "aliases": ["tally", "bookkeeping", "gst filing", "taxation",
                                                    "financial reporting"]},
    "sales": {"category": "other", "aliases": ["business development", "lead generation", "crm",
                                               "salesforce", "cold calling", "client acquisition"]},
    "human resources": {"category": "other", "aliases": ["recruitment", "talent acquisition", "onboarding",
                                                         "payroll", "hr operations"]},

    # ---- soft skills ----
    "teamwork": {"category": "soft", "aliases": ["team player", "collaboration", "collaborative",
                                                 "cross functional team", "worked in a team",
                                                 "pair programming"]},
    "communication": {"category": "soft", "aliases": ["communication skills", "verbal communication",
                                                      "written communication", "presentation skills",
                                                      "stakeholder communication"]},
    "agile": {"category": "soft", "aliases": ["scrum", "kanban", "sprint", "stand up", "agile methodology",
                                              "sprint planning", "retrospective"]},
    "leadership": {"category": "soft", "aliases": ["team lead", "led a team", "mentoring", "mentored",
                                                   "coordinator", "club president"]},
    "learning agility": {"category": "soft", "aliases": ["quick learner", "fast learner", "self taught",
                                                         "self learner", "eager to learn", "curiosity"]},
}


@dataclass(frozen=True)
class Skill:
    name: str
    category: str
    aliases: tuple[str, ...] = ()
    implies: tuple[str, ...] = ()
    related: tuple[str, ...] = ()


class SkillGraph:
    """Indexed, validated view over ``_ONTOLOGY``."""

    def __init__(self, ontology: dict[str, dict] | None = None):
        raw = ontology if ontology is not None else _ONTOLOGY
        self.skills: dict[str, Skill] = {}
        for name, spec in raw.items():
            canonical = normalize(name)
            self.skills[canonical] = Skill(
                name=canonical,
                category=spec.get("category", "other"),
                aliases=tuple(sorted({normalize(a) for a in spec.get("aliases", [])} - {canonical})),
                implies=tuple(normalize(x) for x in spec.get("implies", [])),
                related=tuple(normalize(x) for x in spec.get("related", [])),
            )

        # Surface form -> canonical skill. Longest phrases win during scanning.
        self.alias_index: dict[str, str] = {}
        for skill in self.skills.values():
            for surface in (skill.name, *skill.aliases):
                # First writer wins, so a canonical name is never shadowed by
                # another skill's alias.
                self.alias_index.setdefault(surface, skill.name)

        self.max_phrase_len = max(len(s.split()) for s in self.alias_index)

        # Symmetrize ``related`` and drop edges pointing at unknown skills.
        self._implies: dict[str, set[str]] = {n: set() for n in self.skills}
        self._related: dict[str, set[str]] = {n: set() for n in self.skills}
        for name, skill in self.skills.items():
            self._implies[name] |= {t for t in skill.implies if t in self.skills}
            for target in skill.related:
                if target in self.skills:
                    self._related[name].add(target)
                    self._related[target].add(name)

    # -- graph queries ------------------------------------------------------
    def implies(self, name: str, depth: int = 2) -> set[str]:
        """Transitive closure of implication edges (Next.js -> React -> JavaScript)."""
        seen: set[str] = set()
        frontier = {name}
        for _ in range(depth):
            frontier = {t for f in frontier for t in self._implies.get(f, ())} - seen - {name}
            if not frontier:
                break
            seen |= frontier
        return seen

    def related(self, name: str) -> set[str]:
        return set(self._related.get(name, ()))

    def category(self, name: str) -> str:
        skill = self.skills.get(name)
        return skill.category if skill else "other"

    def is_known(self, name: str) -> bool:
        return name in self.skills

    def canonical(self, surface: str) -> str | None:
        return self.alias_index.get(normalize(surface))

    def evidence_for(self, requirement: str) -> dict[str, float]:
        """Skills that count as evidence for ``requirement``, with credit weights."""
        weights = {requirement: 1.0}
        for name in self.skills:
            if requirement in self.implies(name):
                weights[name] = max(weights.get(name, 0.0), IMPLIED_CREDIT)
        for name in self.related(requirement):
            weights[name] = max(weights.get(name, 0.0), RELATED_CREDIT)
        return weights


SKILL_GRAPH = SkillGraph()
