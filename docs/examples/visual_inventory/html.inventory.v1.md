# Visual inventory v1

Document: material_doc:56ef57d1834c547f58733b6943a0974b0b948296f565e1ae1410f69df343b577
Course: cs50_python; lectures: synthetic-lecture
Material: material:9cb932eed0baa29f25c85b8da1540d0c1915889d37d4a964fc74e2257258a314
Raw SHA-256: 666653abb175ec507132a97ef75bac892d1ec06262f9597d7c39b9e82d7b7d31
Raw scan: complete; assets: 12; verified local occurrences: 2; reference only: 4; possible review cases: 12

Technical observations only; no OCR, diagram interpretation or mathematical verification.

| Type | Count |
| --- | ---: |
| external_image_reference | 5 |
| inline_svg | 1 |
| raster_image | 2 |
| unknown_visual | 4 |

| Page | Count |
| --- | ---: |
| dom_or_unknown | 12 |

| Asset | Position | Type | Extraction | Artifact |
| --- | --- | --- | --- | --- |
| visual_asset:42dbbc96e6311461afed45d296c582f15c576226ae7d9d5ed912dde67bbda850 | {'dom': '/html[1]/body[1]/main[1]/figure[1]/img[1]'} | raster_image | available | verified |
| visual_asset:cefb60f5a99a1f58cd6553e09358be08901cf4c8dad3474245f4cade8fbfa4a8 | {'dom': '/html[1]/body[1]/main[1]/img[1]'} | raster_image | available | verified |
| visual_asset:2cafdc42782c98e7d2b1d85239fcaf07659fadf16c1935bff121fd40b426b46c | {'dom': '/html[1]/body[1]/main[1]/img[2]'} | external_image_reference | reference_only | not_declared |
| visual_asset:cf560a35066271883501c00a66e90b04ca43a5817c6a14f9e78817539b56a8d1 | {'dom': '/html[1]/body[1]/main[1]/img[3]'} | external_image_reference | reference_only | not_declared |
| visual_asset:aedf9d720c1d4a89787303677dcfb4f97d728356b5da5b7d58cb9ecd50ddf80f | {'dom': '/html[1]/body[1]/main[1]/img[6]'} | external_image_reference | unsupported | not_declared |
| visual_asset:19b4a08049f75e51e99a428e186ad37f4bee59b5c9df44e2ec5eed45d08855fd | {'dom': '/html[1]/body[1]/main[1]/img[7]'} | external_image_reference | unsupported | not_declared |
| visual_asset:a55971bbd78f092267ef89085d88656b9dadf51279723bc327d0cea06ccd07fc | {'dom': '/html[1]/body[1]/main[1]/svg[1]'} | inline_svg | reference_only | not_declared |
| visual_asset:52402a9a4b3dd42ff192c30eece193bf3771d47f3d472a6ab8ec0d86b6e94468 | {'dom': '/html[1]/body[1]/main[1]/object[1]'} | external_image_reference | reference_only | not_declared |
| visual_asset:833230794eab3c93b7a5b84bce3df0c6c839cb6e01e83ca7a2b2b6683f3c9f17 | {'dom': '/html[1]/body[1]/main[1]/img[4]'} | unknown_visual | unsupported | not_declared |
| visual_asset:83013fae83e44c271c13c6f83ee6d6ea3037293f48d3c124bd89a022a18475af | {'dom': '/html[1]/body[1]/main[1]/img[5]'} | unknown_visual | unsupported | not_declared |
| visual_asset:597a6121dec9412fb2de96b706567522a1f9be5fb16d4e4f128077bab1abc5d7 | {'dom': '/html[1]/body[1]/main[1]/picture[1]/source[1]'} | unknown_visual | unsupported | not_declared |
| visual_asset:d4db738cc8980ba1bc9641fd2b6103f8671c367cb6fc814bc383e7c4187fee77 | {'dom': '/html[1]/body[1]/main[1]/picture[1]/img[1]'} | unknown_visual | unsupported | not_declared |

## Findings

- warning binding_not_independently_verified: Course/section/lecture mapping preserved from normalized binding; no discovery plan supplied
- warning parser_warning: Browser-local image reference; original remote URL unknown
- visual_asset:42dbbc96e6311461afed45d296c582f15c576226ae7d9d5ed912dde67bbda850 {'dom': '/html[1]/body[1]/main[1]/figure[1]/img[1]'}: warning inline_reference_only: Inline source retained; inventory does not decode or publish image bytes
- visual_asset:cefb60f5a99a1f58cd6553e09358be08901cf4c8dad3474245f4cade8fbfa4a8 {'dom': '/html[1]/body[1]/main[1]/img[1]'}: warning inline_reference_only: Inline source retained; inventory does not decode or publish image bytes
- visual_asset:aedf9d720c1d4a89787303677dcfb4f97d728356b5da5b7d58cb9ecd50ddf80f {'dom': '/html[1]/body[1]/main[1]/img[6]'}: warning unsafe_reference: Non-HTTP(S), credential-bearing or invalid image reference; never dereferenced
- visual_asset:aedf9d720c1d4a89787303677dcfb4f97d728356b5da5b7d58cb9ecd50ddf80f {'dom': '/html[1]/body[1]/main[1]/img[6]'}: warning unsafe_reference: Non-HTTP(S), credential-bearing or invalid image reference; never dereferenced
- visual_asset:19b4a08049f75e51e99a428e186ad37f4bee59b5c9df44e2ec5eed45d08855fd {'dom': '/html[1]/body[1]/main[1]/img[7]'}: warning unsafe_reference: Non-HTTP(S), credential-bearing or invalid image reference; never dereferenced
- visual_asset:19b4a08049f75e51e99a428e186ad37f4bee59b5c9df44e2ec5eed45d08855fd {'dom': '/html[1]/body[1]/main[1]/img[7]'}: warning unsafe_reference: Non-HTTP(S), credential-bearing or invalid image reference; never dereferenced
- visual_asset:a55971bbd78f092267ef89085d88656b9dadf51279723bc327d0cea06ccd07fc {'dom': '/html[1]/body[1]/main[1]/svg[1]'}: warning not_in_normalized_images: Raw-source visual observation supplements the unchanged normalized document
- visual_asset:a55971bbd78f092267ef89085d88656b9dadf51279723bc327d0cea06ccd07fc {'dom': '/html[1]/body[1]/main[1]/svg[1]'}: warning svg_not_rendered: Inline SVG markup position retained; no rasterization or standalone artifact created
- visual_asset:52402a9a4b3dd42ff192c30eece193bf3771d47f3d472a6ab8ec0d86b6e94468 {'dom': '/html[1]/body[1]/main[1]/object[1]'}: warning not_in_normalized_images: Raw-source visual observation supplements the unchanged normalized document
- visual_asset:833230794eab3c93b7a5b84bce3df0c6c839cb6e01e83ca7a2b2b6683f3c9f17 {'dom': '/html[1]/body[1]/main[1]/img[4]'}: warning not_in_normalized_images: Raw-source visual observation supplements the unchanged normalized document
- visual_asset:833230794eab3c93b7a5b84bce3df0c6c839cb6e01e83ca7a2b2b6683f3c9f17 {'dom': '/html[1]/body[1]/main[1]/img[4]'}: warning missing_image_source: Missing/empty image source; no reference inferred
- visual_asset:83013fae83e44c271c13c6f83ee6d6ea3037293f48d3c124bd89a022a18475af {'dom': '/html[1]/body[1]/main[1]/img[5]'}: warning not_in_normalized_images: Raw-source visual observation supplements the unchanged normalized document
- visual_asset:83013fae83e44c271c13c6f83ee6d6ea3037293f48d3c124bd89a022a18475af {'dom': '/html[1]/body[1]/main[1]/img[5]'}: warning missing_image_source: Missing/empty image source; no reference inferred
- visual_asset:597a6121dec9412fb2de96b706567522a1f9be5fb16d4e4f128077bab1abc5d7 {'dom': '/html[1]/body[1]/main[1]/picture[1]/source[1]'}: warning not_in_normalized_images: Raw-source visual observation supplements the unchanged normalized document
- visual_asset:597a6121dec9412fb2de96b706567522a1f9be5fb16d4e4f128077bab1abc5d7 {'dom': '/html[1]/body[1]/main[1]/picture[1]/source[1]'}: warning missing_image_source: Missing/empty image source; no reference inferred
- visual_asset:597a6121dec9412fb2de96b706567522a1f9be5fb16d4e4f128077bab1abc5d7 {'dom': '/html[1]/body[1]/main[1]/picture[1]/source[1]'}: warning srcset_not_selected: Responsive image selection is not evaluated; original srcset retained
- visual_asset:d4db738cc8980ba1bc9641fd2b6103f8671c367cb6fc814bc383e7c4187fee77 {'dom': '/html[1]/body[1]/main[1]/picture[1]/img[1]'}: warning not_in_normalized_images: Raw-source visual observation supplements the unchanged normalized document
- visual_asset:d4db738cc8980ba1bc9641fd2b6103f8671c367cb6fc814bc383e7c4187fee77 {'dom': '/html[1]/body[1]/main[1]/picture[1]/img[1]'}: warning missing_image_source: Missing/empty image source; no reference inferred
- visual_asset:d4db738cc8980ba1bc9641fd2b6103f8671c367cb6fc814bc383e7c4187fee77 {'dom': '/html[1]/body[1]/main[1]/picture[1]/img[1]'}: warning srcset_not_selected: Responsive image selection is not evaluated; original srcset retained
