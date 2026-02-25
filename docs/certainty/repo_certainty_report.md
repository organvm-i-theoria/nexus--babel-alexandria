# Repository Certainty Report

- Generated: `2026-02-25T01:54:26.636731+00:00`
- Files processed: `144`
- Feature/use-case entries: `95`
- Feature status split: `{'implemented': 10, 'planned': 85}`

## Ingestion Guarantees

- Every tracked file was read as bytes and hashed (`sha256`).
- Text files were decoded and scanned for conflict markers and requirement cues.
- PDF files were parsed for page count and text-char extraction when parser support was available.

### Conflict Markers Found

- None

## Feature/Use-Case Ledger Summary

| Type | Count |
|---|---:|
| `api_endpoint` | 10 |
| `roadmap_task` | 48 |
| `suggested_feature_or_use_case` | 37 |

## File Manifest

| Path | Kind | Bytes | Lines | SHA256 |
|---|---|---:|---:|---|
| `.env.example` | `text` | 1275 | 28 | `bd513bc016ad4f743b8da76509955de642431e582008bcbbf253d84f337a2e4a` |
| `.github/AGENTS.md` | `text` | 834 | 24 | `1de9ad6c131630c992313eeb6fb5eaba74846cfa2f1588d3931b6d73c3875c13` |
| `.github/GEMINI.md` | `text` | 957 | 19 | `c5b13e45745ce4c076bf2f0e9513f46c2b98fed22f08fd03e6ae52f106f95fb8` |
| `.github/SECURITY.md` | `text` | 659 | 25 | `caa97e5ccbd5a6df132e0e746ee26c3466d3a8846c3f1821d0282a069d482ad0` |
| `.github/SUPPORT.md` | `text` | 527 | 14 | `f50510518415c2dd8542c6f5df3a6733569fcef57248b76559e81fea74959a8f` |
| `.github/workflows/ci-minimal.yml` | `text` | 1836 | 48 | `7b2815104492c963854e9360561dc87db07baa3347c5b1c4c17871f237fc8413` |
| `.gitignore` | `text` | 609 | 68 | `e8bcab25f2bf6dcd69f95a4a3799bfc7f3f0fe840fa95ce879a6d65c62567f26` |
| `AGENTS.md` | `text` | 763 | 22 | `e1a4e2d026f7402b861674bb5615f9a56f9f14b7d3f3c781851cffe304a71756` |
| `CLAUDE.md` | `text` | 14282 | 206 | `9bc0059fbd3f785861229e05778a1e9b5bead10d039b11bf414135c015e81809` |
| `GEMINI.md` | `text` | 957 | 19 | `06f4ee20523b516b296c427463c6ad891e9f242f3bc8693b18fdbee13011f0ac` |
| `LICENSE` | `text` | 1064 | 22 | `6d319436c6a6428d1cfa592e3386aef31cb02e04d67731a577b68395c5e963fc` |
| `MANIFEST.yaml` | `text` | 73790 | 1931 | `eabc9892bf75038588d9e77eec64f4b4dd28cf28bbee7c376d4654b95def5d08` |
| `Makefile` | `text` | 491 | 27 | `fe109810491c89d1a4c8bbe54c84d5840963af5d5f4c4fb1001647f861a55490` |
| `README.md` | `text` | 40290 | 410 | `3e2ec4cb329c172e4d07435b63bdef0da50bf7af90cbf1467806c39fc6c82622` |
| `alembic.ini` | `text` | 570 | 38 | `10cbd807a4fd691b24ef067c98e10ca269c0455c11f3fdd16dcf9c2bf30bc4fc` |
| `alembic/env.py` | `text` | 1258 | 48 | `ca979c9c3923b76f89d216b92636f6c759cffee075b8f7c0117f984b020356ae` |
| `alembic/script.py.mako` | `text` | 546 | 27 | `45b179250bf89ed063fb4304fa9e0c23979e7126daf8937177e85b6cbcd10829` |
| `alembic/versions/20260218_0001_initial.py` | `text` | 12545 | 256 | `42df7dc07338810fb9fdfc643331408a70b09002fbce90abf7aff9771935fb63` |
| `alembic/versions/20260218_0002_wave2_alpha.py` | `text` | 10681 | 192 | `f194976c970a02e5366d3106b7f249c4bf62152bebbe5fe0096d719c224ae2fc` |
| `alembic/versions/20260223_0003_add_atom_metadata.py` | `text` | 512 | 26 | `ac5c157b935866408af12724ade29e4fad77391d9316af1ebbdc7b0f70347878` |
| `alembic/versions/20260225_0004_remix_artifacts.py` | `text` | 6634 | 108 | `68bbe5416e3c3e2290865e15cca448b1ae87c73785123849d7585bd9d747ea3c` |
| `corpus/seeds/.gitkeep` | `text` | 0 | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `docker-compose.yml` | `text` | 621 | 30 | `54cdfe4abe9f459b2ab433d0ad9aa73c3da37f844a420953b8ea97980301bd36` |
| `docs/.nojekyll` | `text` | 0 | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `docs/OPERATOR_RUNBOOK.md` | `text` | 4149 | 168 | `8f1cd1cdec11d300239fd73cc6d3f6a644b8285c7f856488595d8829c999c4e8` |
| `docs/alexandria_babel/AB-PLAN-01_Build_Tickets.json` | `text` | 7205 | 193 | `7dcd8b8ef592e01361f3ee5212962b4637d264ce23df6cccae6057d470bc2a80` |
| `docs/alexandria_babel/AB-PLAN-01_Build_Tickets.md` | `text` | 9201 | 271 | `1725a01824fa9c0330574249cc02c47137d01f2b2d96e3941c3d92ebf65f658b` |
| `docs/alexandria_babel/Organism_Blueprint.md` | `text` | 1820 | 44 | `e54874fb6e1d72bd12aadefdc2bd538d6dbc3e53ef799b1c6175b2bef6fab563` |
| `docs/alexandria_babel/Protocol_Tracker.md` | `text` | 1125 | 27 | `b3df4987793cbb8c7edd0c29365d3e164f62a43ac793489350bde5c401e14c02` |
| `docs/alexandria_babel/Prototype_Tracker.md` | `text` | 2047 | 36 | `90f0b610dc4dc4af46fd2bcb3025c78d52970be91839457697a3b402ce93882e` |
| `docs/alexandria_babel/Save_Receipt_2026-02-18.md` | `text` | 831 | 15 | `404b5075336832ebe9ec1911dea5b99f8353ad35cf69b4b9298858bbb2858f8f` |
| `docs/alexandria_babel/Thread_Plan_Academic.md` | `text` | 274 | 11 | `5ecba6fde374cb7bb4f71709478c294612231599a9a774c62d00470dc7a9189f` |
| `docs/alexandria_babel/Thread_Plan_Funding.md` | `text` | 269 | 11 | `7384c8cb4d8d8bc9e1032039f8db3bd6d1ee17288e6636a1944214fa678ea95c` |
| `docs/alexandria_babel/Thread_Plan_UX.md` | `text` | 227 | 11 | `de5c8ae1a4791de14531cf1823355d0da05ee729c47e2e7328c5b5d7a7b491a3` |
| `docs/alexandria_babel/feature_usecase_ledger.json` | `text` | 109553 | 2808 | `22882acb74eafbd45570aa3a1f3eec289cf8da78859dead3e7dfd884497816cd` |
| `docs/alexandria_babel/feature_usecase_matrix.md` | `text` | 57971 | 308 | `033260940de7ce0531ca55b5050d17872a35174182a7a9eced329ca940459cb2` |
| `docs/alexandria_babel/index.md` | `text` | 1033 | 19 | `98955cd522756ed03f848e5d91b99465389fc594a8b050ac0c7b45a305d61fac` |
| `docs/alexandria_babel/seed_corpus_registry.yaml` | `text` | 1129 | 38 | `034d41fd10a2f77fec9ddf56501b0b75eba606ff9f5919840fb64bb7507b502e` |
| `docs/corpus/# Theoria Linguae Machina Comprehensive Design Document for the….md` | `text` | 51702 | 894 | `9beea098ab6cc29314b670615d788288f672dd5d56abae5068dfecf0fdc3cab6` |
| `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | `text` | 81969 | 2250 | `e54720b7e5e3af43da08e31a9bdc003f8e2955cf20046082f87b8f706d13ed74` |
| `docs/corpus/Nexus_Bable-Alexandria.md` | `text` | 54588 | 890 | `e967fe463e7041f647c65cc8fa9c146065d41af470007f5c6f1acf30f82e1f80` |
| `docs/corpus/The Archive of the Trace.pdf` | `pdf` | 138128 | - | `2d94f3947f9850c28b3ea4d20c2fc6f74958bbe2f47e07954bb02e9e2f38c4a8` |
| `docs/corpus/The Brutalist Ziggurat of Truth.pdf` | `pdf` | 123375 | - | `db8af2aa9163a33df86abee911c2f644160ea8872d3fab377800228addae3938` |
| `docs/corpus/the-archive-trace.md` | `text` | 10948 | 71 | `36cc81768edf3e94704d5900a7aa0174647bea211b54fa24070095dd825841e4` |
| `docs/corpus/the-brutalist-ziggurat-of-truth.md` | `text` | 7973 | 79 | `bb743de5b5a82f693ff1fb76f3d9957e985a42e29e8bdaa33367aac491818fe6` |
| `docs/index.html` | `text` | 299 | 13 | `4af5eb29efaf6c79a4844757b84be6315f1928662d56319e1b7d920f7b5364b4` |
| `docs/pitch/index.html` | `text` | 58581 | 1171 | `4304fd7cf3d9bdf45f61f4015b8e108579c64f1b4e07f6dc38450d204d658724` |
| `docs/prix_ars_2026/architecture_9_layer_plexus.mmd` | `text` | 940 | 17 | `45fc829baf0786c57b2b1a87f580a1bcf8b730aaeb61b5dc84739a7b7798630f` |
| `docs/prix_ars_2026/architecture_diagram_notes.md` | `text` | 1090 | 28 | `b9dcaecf101a0b694ea52a25010cffa500ec5d57661ab1dfd597a4fd79e643cf` |
| `docs/prix_ars_2026/demo_video_runbook.md` | `text` | 2251 | 79 | `6b45bd11a95caed61851378ce12a9e168f9ab05f097aa0e833afe433deb156fb` |
| `docs/reviews/evaluation_to_growth_2026-02-25.md` | `text` | 14874 | 337 | `e9f0e047d1c0777491d8e5bcac25542b1794f5464e3aba62d408e50991ab9cb6` |
| `docs/roadmap.md` | `text` | 20844 | 1003 | `a7f47ace061f4af8f04cd59f3424d53b7f0aaf83f4bdad97dc0feef472696f25` |
| `docs/roadmap_mvp_next.md` | `text` | 4544 | 145 | `a45932ee18364030d3810987395fce63eb6d38a15212ad28f23666f15a42020e` |
| `pyproject.toml` | `text` | 936 | 49 | `de0a421c491a99d3047a3fe798f36061112a53f3351f045f18fe6ee2b7c891ac` |
| `scripts/alexandria_babel_alignment.py` | `text` | 13948 | 359 | `5cb14497811b005aee06701d434afd3e00682c98e51900de4db11c33f5030313` |
| `scripts/demo_sequence.py` | `text` | 10806 | 264 | `442ac9e5190e14fd3c6b0287fe16ad989a2f7f2d60dddeba578680dc00c90bb0` |
| `scripts/export_atom_library.py` | `text` | 5444 | 140 | `0a7b00bc5a44752ac15b2e79628a1237177af611a61a0f06a13f9775fcb9ff68` |
| `scripts/generate_openapi_contract_snapshot.py` | `text` | 2148 | 61 | `aaf38135190d996850e007b25c409a1a6c3cb6e8ad04a6da6ab55eb1c962fb9b` |
| `scripts/ingest_corpus.py` | `text` | 5141 | 136 | `f2306762ce162679edbe655212d702c994c9b6d06c5706fcee03ec6e4bd84df7` |
| `scripts/load_test.py` | `text` | 1391 | 37 | `871ef79b46d4395b0c5666b27d6e81c8de344c4c086157c6bd524233eeae4576` |
| `scripts/render_architecture_diagram.py` | `text` | 5346 | 136 | `587d5ed935936bbbd9443b1d8ff87ada16ae32c883e19c02c2109f5b636c12fb` |
| `scripts/repo_certainty_audit.py` | `text` | 16897 | 445 | `b7ed92ac179e09a308847793a97b42258c545dd99b1022e9e440e532bd55e284` |
| `scripts/run_api.sh` | `text` | 103 | 4 | `ef5c1e6448a8a103d3e4639927be0617cbd5d4a143cfbe23193b8c2980638e0c` |
| `scripts/visualize_atoms.py` | `text` | 9889 | 250 | `e5faac7df16778083e5e3d7afb34b036acb7ea175ff12084b718fa787131d58d` |
| `seed.yaml` | `text` | 1094 | 42 | `2937e7625e3495a0233aa3e29b91dd3d27a65c8ef3029b7254a4da1115d13f92` |
| `specs/01-ingestion-atomization/plan.md` | `text` | 18553 | 408 | `96e6049254a577da6aec54c9c675aeb259c18d9942a6517f14ac67f43d9ce75e` |
| `specs/01-ingestion-atomization/spec.md` | `text` | 28811 | 431 | `874734a508493a604e4bd276e42935dd01772419795ef7f158fded2a73f98422` |
| `specs/01-ingestion-atomization/tasks.md` | `text` | 18207 | 425 | `76ce71c753c92e047b49758d9b6266ce746df364c69e004ccd8d4722957bbcfd` |
| `specs/02-linguistic-analysis/plan.md` | `text` | 17258 | 369 | `63360e719a1545f15ca02353828c61aa054eda03dd14d316acb41fc78463630e` |
| `specs/02-linguistic-analysis/spec.md` | `text` | 28481 | 516 | `495c742b21041215e8531bf508b9db7199bf79ad3b0f9920ceee9f95eac7eeb7` |
| `specs/02-linguistic-analysis/tasks.md` | `text` | 27727 | 432 | `b77234d35a53e45454b3577da3051cc46fa13192797847e89f9f44025f7de644` |
| `specs/03-evolution-branching/plan.md` | `text` | 28256 | 784 | `32090d2464189bcb148594bb659eaa3fb9b6aab440ed7e63a8bc48273bbb9d50` |
| `specs/03-evolution-branching/spec.md` | `text` | 37317 | 584 | `9253b65e0673c887c82085084a6b9d830695765ad7ee2419907470ed49868355` |
| `specs/03-evolution-branching/tasks.md` | `text` | 32818 | 547 | `c11c6fe78b38cdce1facd877abaad5d746b9468aff93d5ca084d0cbdcbf3e0f8` |
| `specs/04-remix-recombination/plan.md` | `text` | 21591 | 451 | `2e3303e47176cbac388566231c07e002eace751996961268ef3f9b5f450ba279` |
| `specs/04-remix-recombination/spec.md` | `text` | 28330 | 390 | `c0249b8863e37bc4ab65889af6852d1bee1ed87f04c05ebc6b48f00b8dfa8a56` |
| `specs/04-remix-recombination/tasks.md` | `text` | 25264 | 544 | `7f88873dcc4e2455aa22cb5573cdcaa1fbf33c63b107f02d1fe7eb3f336f6456` |
| `specs/05-governance-audit/plan.md` | `text` | 20183 | 459 | `c5e2d5d833ec011cae35faedab3208fda48466d9060bb42ca07ee135a95aeb4f` |
| `specs/05-governance-audit/spec.md` | `text` | 32264 | 430 | `636c470808ab0f47aabb4b440526c94e18b106c84e1d036ad988cdd79b71a567` |
| `specs/05-governance-audit/tasks.md` | `text` | 23230 | 465 | `df699063443f28345de83bf65609076682afe39f6705958d3699a426dbc1cb3b` |
| `specs/06-seed-corpus/plan.md` | `text` | 18195 | 461 | `ec68983423b67bc0eec1aabcf648ec6b426650d1cb2d82fac0751c856816a58f` |
| `specs/06-seed-corpus/spec.md` | `text` | 27854 | 375 | `af04fd851ea2159ec9e5b4121c43ad4d8cb8a4284d7e30e59b8de93560878e12` |
| `specs/06-seed-corpus/tasks.md` | `text` | 20441 | 453 | `983729ffaeeb0afb6de427634b3c455736960e32d0835aba8b352667e1d2fe44` |
| `specs/07-hypergraph/plan.md` | `text` | 17115 | 399 | `312a507cbbdb7d9da273bb2a2df4e4a651b7cf56290eafce3c8f049c6e13a676` |
| `specs/07-hypergraph/spec.md` | `text` | 30859 | 426 | `27396c220a4d6512b3ced61dc27a64c441f2f1cc2faf6cc9b44719cc5d711f3c` |
| `specs/07-hypergraph/tasks.md` | `text` | 23007 | 478 | `d40366ad1e5319b945db0c2a5d2b26d96cfd96b13e34745702c33f008d68b1e1` |
| `specs/08-platform-infrastructure/plan.md` | `text` | 22426 | 593 | `423f97a0355e3dde9c4caec5f2b45783d7e4898285d3d2cead4ecc461bd8ddc8` |
| `specs/08-platform-infrastructure/spec.md` | `text` | 35333 | 553 | `0464feea32192d19ec92a8cffa45c0936c0367fc6a36c0fd4d142351bcd2c515` |
| `specs/08-platform-infrastructure/tasks.md` | `text` | 21172 | 359 | `b944304e39d0186d753ec082c54bc2e2bf57a139bdba7fe5ccf69605facdb1eb` |
| `specs/09-explorer-ux/plan.md` | `text` | 32019 | 763 | `ff8c84d666ead04e862ec38b849927f15ec690b0469032f9a9b490acc13ce8f3` |
| `specs/09-explorer-ux/spec.md` | `text` | 36690 | 585 | `d8ef00aef7d2e556681481e7670cabbd343b813c1ee06b43578f1f9503d86df3` |
| `specs/09-explorer-ux/tasks.md` | `text` | 29749 | 642 | `be9b3c9f5cf2e6ce794c9bd458991be44a5fd82e1fa3b4e4cf700beba23c9412` |
| `src/nexus_babel/__init__.py` | `text` | 19 | 2 | `7d747afc2b886329d5e309a87e59ee8f3eb222fac210351c79bb0742ee11c426` |
| `src/nexus_babel/api/__init__.py` | `text` | 0 | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `src/nexus_babel/api/deps.py` | `text` | 1471 | 45 | `a353c56de5ea1d4ba401f88242bf2c525673263c7a2638718f2f020673dbdffc` |
| `src/nexus_babel/api/errors.py` | `text` | 2167 | 67 | `1adb57228c332bce0fb2ef8c110a0a54f467c897b574761c5c9b3ee7c5793bba` |
| `src/nexus_babel/api/openapi_contract.py` | `text` | 2277 | 74 | `b594b049b3df27f388261c9b6097f8a72b4ebd0f75ee21f003359efef121418a` |
| `src/nexus_babel/api/routes/__init__.py` | `text` | 854 | 26 | `70af20097b4b44c73105dbd6c76ff7d11253cd19325629f3184ef5bb9aea0228` |
| `src/nexus_babel/api/routes/analysis.py` | `text` | 6295 | 168 | `c4ab9c97d09ce28540558d8daf4bf2565845ede925ca1d7442c6a9dd75b9935a` |
| `src/nexus_babel/api/routes/auth.py` | `text` | 833 | 28 | `a6e6e23d33f92a6455af6f6af62a284039eb49c72753de739ffa36c6c839e3d4` |
| `src/nexus_babel/api/routes/branches.py` | `text` | 4752 | 129 | `230424516eccda429c32e8c8f793d2b3a041502e11e91d06c3ca556294db13ac` |
| `src/nexus_babel/api/routes/documents.py` | `text` | 3366 | 94 | `c5184bf3a5dd5ae7b2779935f4382c84439fe3099df8652810eebe9df2962624` |
| `src/nexus_babel/api/routes/governance.py` | `text` | 1892 | 52 | `481f57d1b730c2a5cb66d6634bea8c18fe0da894304d1a6b1b895925c1bed6c8` |
| `src/nexus_babel/api/routes/ingest.py` | `text` | 4629 | 121 | `5a4dab6816563f6e362f3d3e2a401e79992ec3a91ea5fdb0c166b4845df84e5e` |
| `src/nexus_babel/api/routes/jobs.py` | `text` | 4019 | 110 | `f02c77becf88c866ff844eb72d2d6012169ddc1b32db8c2a4d164da2a88512f5` |
| `src/nexus_babel/api/routes/remix.py` | `text` | 5250 | 141 | `7c5f39bac64bfc7b679adeeb753f9605c83fcbd6d3b94eae12d5bde4e2b641d5` |
| `src/nexus_babel/config.py` | `text` | 2326 | 61 | `86654c105e7d37aa39f39525c722d17bc219d8956a31a62a473bc898f9b366a3` |
| `src/nexus_babel/db.py` | `text` | 1039 | 31 | `edfc4f3086798cf489e2f18805202ecdaeceba056ee9778d99a01d7000031341` |
| `src/nexus_babel/frontend/templates/shell.html` | `text` | 12456 | 358 | `d3fe6d15d8e5d24152039103c371747ae5542073fbebdb9c9ffafb1b96d63ecb` |
| `src/nexus_babel/main.py` | `text` | 7144 | 175 | `2b9bf8e71b8fb242ef16b6186590deb572e5dc5248d651e20a1a77075b6e6059` |
| `src/nexus_babel/models.py` | `text` | 19022 | 359 | `15cb38cdc30faeae4269b31b41c9bb2f27fd6589ba2315a7672483b4de61e834` |
| `src/nexus_babel/schemas.py` | `text` | 9492 | 357 | `fb6ebdced0974a425e41b1c247f0d56bfda0956efea99ecc4908f89cfbc834e6` |
| `src/nexus_babel/services/__init__.py` | `text` | 0 | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `src/nexus_babel/services/analysis.py` | `text` | 11004 | 271 | `0ccfcc5f1882b04619bb3978f0a42d7881d375f9b9206770c865f59ffe552476` |
| `src/nexus_babel/services/auth.py` | `text` | 2525 | 77 | `a70037cf62cbbdca9e1aa89054b1b8481e5f5d5be558beb8c673776ef2410baf` |
| `src/nexus_babel/services/canonicalization.py` | `text` | 3189 | 104 | `7b4fea277864f6dee507cdb35c982863d303eec48be63a33b496818fde5e855d` |
| `src/nexus_babel/services/evolution.py` | `text` | 15978 | 399 | `5b6933e80cea7b35aafca895390deccfa6a2b1a2eba5800b0cb147a044485e60` |
| `src/nexus_babel/services/glyph_data.py` | `text` | 6157 | 164 | `56f6188f1a6428ed74361926f2e1f4a4922f61af995b7a5347e1deb324483fa6` |
| `src/nexus_babel/services/governance.py` | `text` | 5639 | 155 | `86b4f9dd65d484260b3049316609c716b8a4395a049e747161637f749d5534fd` |
| `src/nexus_babel/services/hypergraph.py` | `text` | 7519 | 192 | `d15c3de807e56ec9b26010086b1293929909bf1659134c4f90c82bca19465f2a` |
| `src/nexus_babel/services/ingestion.py` | `text` | 17567 | 425 | `de312c55c832a4a91b68e41864b72cb35f5a74cb08d9f163953fc2cc21a29035` |
| `src/nexus_babel/services/ingestion_media.py` | `text` | 4225 | 130 | `ca7747b977439c2e50590e6bdd45dc07ac54bd2800724271073d6e584264edd1` |
| `src/nexus_babel/services/ingestion_projection.py` | `text` | 2658 | 76 | `dc3dc8bd75f46d5badc3dc0f0e38a658bb3755f079458d26952fcceea7ee8767` |
| `src/nexus_babel/services/jobs.py` | `text` | 10834 | 279 | `d3b1d60d200c5177ea1357519f56ad471c8825b2434b73dd733295252cf7dc56` |
| `src/nexus_babel/services/metrics.py` | `text` | 1199 | 32 | `609b794428ac883f274015830d2a58baed634ee6fa993b8079b6182efda09a3a` |
| `src/nexus_babel/services/plugins.py` | `text` | 4955 | 158 | `ccf9e18b523a395828821c599a056e08cff5d8f729bbd98f44585cdfa36d7dd9` |
| `src/nexus_babel/services/remix.py` | `text` | 16764 | 417 | `c36ad5e9e4fe45a5ed7ab49cab71d7725e475ccfe9b223fe1b76f74547a2e3b8` |
| `src/nexus_babel/services/remix_artifact_persistence.py` | `text` | 2720 | 89 | `fda68072192d41d59176f872ea0c9cb4d03528420573f9303c1b28e0de4cf58f` |
| `src/nexus_babel/services/remix_artifact_serialization.py` | `text` | 3128 | 87 | `1fb776c59d552bb942adf3555432482f6f9475b0d83a2e6e7b073c074dbb1b43` |
| `src/nexus_babel/services/remix_strategies.py` | `text` | 2670 | 70 | `9a23c3515cacee743201322f4ba9411040c373e5c20bfe5b67b17fe6ccfa840e` |
| `src/nexus_babel/services/rhetoric.py` | `text` | 2333 | 71 | `8dc30544e676ea5c07c670f684fc7567d849ff2633eb3bfaf66d051119a7ba7c` |
| `src/nexus_babel/services/seed_corpus.py` | `text` | 7179 | 197 | `d109d425a1675acbbd6bebb2a9a60fd39c76c063586c003030c0836bb7b96ee9` |
| `src/nexus_babel/services/text_utils.py` | `text` | 7685 | 230 | `fc6442f25ccda3197de01c33295e7e3cf11c53e3d45b5710b28548fc71e31de9` |
| `src/nexus_babel/worker.py` | `text` | 1439 | 49 | `081430c11e21bcf79d7a8c0102fda78eb88f921bbe53ce76e345c8fa602571d9` |
| `tests/conftest.py` | `text` | 2687 | 92 | `bfcd1230773c46a2fec5b5507741570f765090a02d1abd594a95552f1b6ff1cd` |
| `tests/snapshots/openapi_contract_normalized.json` | `text` | 74795 | 3234 | `f50ddf53a140771d26af9e94b5925c502252906c7235e3f5d5e80ec50a19b6c7` |
| `tests/test_ab_plan_01.py` | `text` | 14172 | 374 | `baf9e44ba6c6e9e869a6167e48928a108fcbc6a1318af401128cd99ad7525721` |
| `tests/test_arc4n.py` | `text` | 14924 | 409 | `9bf04cefc72cfd8b5bdf24ed4956de627269653a7a88db4c4cd526d7ed394adf` |
| `tests/test_hardening_runtime.py` | `text` | 4174 | 119 | `2e74927f3475515d9fab15c3a3a49d6d41b4a92242d412fefa939068b6ba747b` |
| `tests/test_mvp.py` | `text` | 20828 | 509 | `c31329955f277c7173e3f869ac0139debf3e23ac944068ffcaae877824eac950` |
| `tests/test_openapi_contract_snapshot.py` | `text` | 545 | 17 | `bf1b7ee69ca442cf49b9f1c7980ba001c52be0cfc65e7d710261a4bad801be66` |
| `tests/test_plugins.py` | `text` | 1633 | 45 | `89783f06b2af0d02412b00de8c6feee6cea6603089b78621daf30f8628a19771` |
| `tests/test_wave2.py` | `text` | 5588 | 152 | `17c2ed71e00b559bcae1d9b4f2bab4c428480668f0996df906f29918d93e38d2` |
| `uv.lock` | `text` | 326885 | 1514 | `19c9eccc9e192e8ca230c71c3f48fd78c0c0a146855fafc23645bd89b9b93d18` |

## Feature/Use-Case Ledger

| ID | Type | Status | Source | Line | Text |
|---|---|---|---|---:|---|
| `endpoint::/api/v1/auth/whoami` | `api_endpoint` | `implemented` | `docs/OPERATOR_RUNBOOK.md` | 81 | /api/v1/auth/whoami |
| `endpoint::/api/v1/ingest/batch` | `api_endpoint` | `implemented` | `docs/OPERATOR_RUNBOOK.md` | 94 | /api/v1/ingest/batch |
| `endpoint::/api/v1/documents` | `api_endpoint` | `implemented` | `docs/OPERATOR_RUNBOOK.md` | 102 | /api/v1/documents |
| `endpoint::/api/v1/ingest/jobs/{job_id}` | `api_endpoint` | `implemented` | `docs/OPERATOR_RUNBOOK.md` | 103 | /api/v1/ingest/jobs/{job_id} |
| `endpoint::/api/v1/hypergraph/documents/{document_id}/integrity` | `api_endpoint` | `implemented` | `docs/OPERATOR_RUNBOOK.md` | 105 | /api/v1/hypergraph/documents/{document_id}/integrity |
| `endpoint::/api/v1/jobs/submit` | `api_endpoint` | `implemented` | `docs/OPERATOR_RUNBOOK.md` | 106 | /api/v1/jobs/submit |
| `endpoint::/api/v1/jobs/{job_id}` | `api_endpoint` | `implemented` | `docs/OPERATOR_RUNBOOK.md` | 107 | /api/v1/jobs/{job_id} |
| `endpoint::/api/v1/analysis/runs/{run_id}` | `api_endpoint` | `implemented` | `docs/OPERATOR_RUNBOOK.md` | 108 | /api/v1/analysis/runs/{run_id} |
| `endpoint::/api/v1/audit/policy-decisions` | `api_endpoint` | `implemented` | `docs/OPERATOR_RUNBOOK.md` | 109 | /api/v1/audit/policy-decisions |
| `endpoint::/api/v1/governance/evaluate` | `api_endpoint` | `implemented` | `docs/OPERATOR_RUNBOOK.md` | 120 | /api/v1/governance/evaluate |
| `ENV-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 21 | Task ENV-001 |
| `ENV-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 66 | Task ENV-002 |
| `ENV-003` | `roadmap_task` | `planned` | `docs/roadmap.md` | 82 | Task ENV-003 |
| `DEP-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 102 | Task DEP-001 |
| `DEP-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 116 | Task DEP-002 |
| `DEP-003` | `roadmap_task` | `planned` | `docs/roadmap.md` | 130 | Task DEP-003 |
| `HG-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 155 | Task HG-001 |
| `HG-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 178 | Task HG-002 |
| `HG-003` | `roadmap_task` | `planned` | `docs/roadmap.md` | 197 | Task HG-003 |
| `SCH-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 216 | Task SCH-001 |
| `SCH-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 234 | Task SCH-002 |
| `PHON-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 259 | Task PHON-001 |
| `PHON-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 279 | Task PHON-002 |
| `PHON-003` | `roadmap_task` | `planned` | `docs/roadmap.md` | 295 | Task PHON-003 |
| `MORPH-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 312 | Task MORPH-001 |
| `MORPH-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 331 | Task MORPH-002 |
| `MORPH-003` | `roadmap_task` | `planned` | `docs/roadmap.md` | 348 | Task MORPH-003 |
| `SYN-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 366 | Task SYN-001 |
| `SYN-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 382 | Task SYN-002 |
| `SYN-003` | `roadmap_task` | `planned` | `docs/roadmap.md` | 398 | Task SYN-003 |
| `SEM-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 415 | Task SEM-001 |
| `SEM-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 430 | Task SEM-002 |
| `SEM-003` | `roadmap_task` | `planned` | `docs/roadmap.md` | 445 | Task SEM-003 |
| `PRAG-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 462 | Task PRAG-001 |
| `PRAG-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 477 | Task PRAG-002 |
| `PRAG-003` | `roadmap_task` | `planned` | `docs/roadmap.md` | 492 | Task PRAG-003 |
| `DISC-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 508 | Task DISC-001 |
| `DISC-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 523 | Task DISC-002 |
| `SOCIO-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 540 | Task SOCIO-001 |
| `SOCIO-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 554 | Task SOCIO-002 |
| `VIS-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 577 | Task VIS-001 |
| `VIS-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 592 | Task VIS-002 |
| `ALIGN-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 609 | Task ALIGN-001 |
| `RHET-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 633 | Task RHET-001 |
| `RHET-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 648 | Task RHET-002 |
| `SEMI-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 665 | Task SEMI-001 |
| `SAFE-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 688 | Task SAFE-001 |
| `SAFE-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 703 | Task SAFE-002 |
| `META-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 727 | Task META-001 |
| `META-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 742 | Task META-002 |
| `VIZ-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 766 | Task VIZ-001 |
| `VIZ-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 781 | Task VIZ-002 |
| `API-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 797 | Task API-001 |
| `TEST-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 822 | Task TEST-001 |
| `TEST-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 839 | Task TEST-002 |
| `DEPLOY-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 863 | Task DEPLOY-001 |
| `DEPLOY-002` | `roadmap_task` | `planned` | `docs/roadmap.md` | 880 | Task DEPLOY-002 |
| `OPT-001` | `roadmap_task` | `planned` | `docs/roadmap.md` | 904 | Task OPT-001 |
| `suggestion::6ffacc499b7c` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 208 | [Next Step Reference ID: ARC4N001-NEXT01] |
| `suggestion::7ce27603ddc5` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 211 | > Would you like me to also propose a file-naming syntax system for maximum future database parsing (e.g., `ODYSSEY_WORD_0001_Sing.txt`)? |
| `suggestion::e5c2b20e0547` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 352 | \| Should we plan an experimental "New Alphabet" generation after first 3 seed texts? \| Yes (pilot program) \| Later (after stability) \| |
| `suggestion::9c591420b1d2` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 356 | # [Next Step Reference ID: ARC4N001-NEXT02] |
| `suggestion::4ceb4f8dc382` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 362 | > Should I proceed to sketch a visual flowchart showing how a single *letter* can mutate into future language forms across ARC4N? |
| `suggestion::917e31e7d63a` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 486 | - **Should we imagine new *sung* languages** (musical syllabic structures) **emerging from ARC4N too?** |
| `suggestion::e4e08d095a81` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 491 | # [Next Step Reference ID: ARC4N001-NEXT03] |
| `suggestion::3feebab7027e` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 493 | :: Awaiting your direction: Which prototype should we build next? :: |
| `suggestion::d21b33f92c10` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 507 | Would you like me to start by fusing **A + E** into a full micro-chain evolution (visual, phonetic, symbolic)? |
| `suggestion::731f1ecda916` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 653 | # [Next Step Reference ID: ARC4N001-NEXT04] |
| `suggestion::5ddcab3c825f` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 664 | (*We can build both eventually, but it will focus this immediate next step.*) |
| `suggestion::80d2a0ff377b` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 673 | Should we also track how the languages in our current reality have shaped and changed to create algorithms and functions to mirror this? English has been around for quite some time, has changed drastically, Italian, Roman, Latin, Japanese, all of these languages have shifted over time. Now, we could be attempting to do a Clockwork Orange and update language how we presuppose it might be, or we could literally create mathematical understandings of how language changes and implement that. Here, in our work, but then also, since this is modular and cellular and automatable, right, we're building a live synthetic machine, which we could, and will automate and will change through natural generative ways and also through unnatural ways via a user. And take natural evolution and ramp it up, right? If you look at the graph of how technology changed things over time, right, it's a greatly upward curve that we just don't understand. Thousands of years, we had somewhat similar access to technology, and then suddenly, digital technology takes us on the upward swing in a way that we are not even able to comprehend. |
| `suggestion::092c4a7a1615` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 826 | # [Next Step Reference ID: ARC4N001-NEXT05] |
| `suggestion::5e3a9280263c` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 832 | \| Which prototype or engine component should we start building next? \| P5 - Natural Historic Drift Model \| P6 - First Synthetic Mutation Trial \| |
| `suggestion::1adaef68c7fb` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 983 | # [Next Step Reference ID: ARC4N001-NEXT06] |
| `suggestion::fc6b00430ac8` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 987 | \|[Would you like me to also pre-draft the text of the public post in case you want it immediately?]\| |
| `suggestion::8a50349804b0` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1116 | ## 7. **What Areas of Study Should We Expand Into for Further Research?** |
| `suggestion::2b4a585ac023` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1175 | # [Next Step Reference ID: ARC4N001-NEXT07] |
| `suggestion::fb01bba58a5e` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1179 | - Or would you like to first quickly draft an internal **Funding Abstract Sentence** to prepare your future grant language? |
| `suggestion::b40e375e40aa` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1293 | # [Next Step Reference ID: ARC4N001-NEXT08] |
| `suggestion::16c4d0953a31` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1405 | ARC4N must model: |
| `suggestion::e0263e8d0b77` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1486 | # [Next Step Reference ID: ARC4N001-NEXT09] |
| `suggestion::e7e12bc2c364` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1490 | - Would you like me to also generate **thread starter templates** for the UX, Academic, and Funding threads using these cartridges? |
| `suggestion::99eb312e486a` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1637 | # [Next Step Reference ID: ARC4N001-NEXT10] |
| `suggestion::7de553e91279` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1640 | - Which new thread would you like to launch first: UX, Academic, Funding, or Other? |
| `suggestion::e2cb04afdb9e` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1641 | - Would you like me to generate first action prompts inside the new thread automatically once launched? (To maintain velocity.) |
| `suggestion::9ce123fadeda` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1753 | # (D) Proposed Immediate Next Steps Post-Meta-Critique: |
| `suggestion::2f3555e4c6ea` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1773 | # [Next Step Reference ID: ARC4N001-NEXT11] |
| `suggestion::f363f17f638e` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1777 | - Would you like me to immediately scaffold the Prototype Tracker file with what we’ve built so far (Language Spiral, Glyph Fusion, Drift Engines, Cartridges)? |
| `suggestion::b3f77383c36c` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1811 | I flagged it as a potential next step. |
| `suggestion::d6d2a2dc73ff` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1954 | \| Action ID \| Next Step \| Result \| |
| `suggestion::0bf3e848b7f5` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1956 | \| [A1] \| Build Prototype Tracker Now \| Full list of all prototyped ideas captured formally \| |
| `suggestion::fd2d1cefa34e` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 1972 | # [Next Step Reference ID: ARC4N001-NEXT12] |
| `suggestion::c7b4ede8802f` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 2037 | **We should immediately SPLIT paths cleanly:** |
| `suggestion::be79b0f1484e` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 2095 | # [Next Step Reference ID: ARC4N001-NEXT13] |
| `suggestion::43deadb007e0` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 2176 | > Which phase of evolution (expansion or compression) should we build first tangible artifacts for? |
| `suggestion::84a9414b108b` | `suggested_feature_or_use_case` | `planned` | `docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md` | 2192 | - Build Prototype Tracker capturing all proposed systems (glyph fusion, drift engines, cartridge systems) |
