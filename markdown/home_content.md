# Extension of Mid‐Season Drainage in Paddy Rice Cultivation
#### *under the J-Credit Scheme's agricultural methodology*

## What is the J-Credit Scheme?
The J-Credit Scheme certifies and makes tradeable the difference between:

1. The amount of greenhouse gas emissions that would have occurred without any reduction activities (the baseline), and
2. The actual emissions after implementing reduction or absorption activities.

That difference, which is measured in tons of CO₂ equivalent, is issued as a credit. Credits can come from reduced emissions or from carbon absorption through activities.

<img src="app/static/concept_of_baseline_and_credit.png">

### How does credit trading work?

- Credit Producers: Those who carry out CO₂-reduction or absorption activities in accordance with an approved J-Credit methodology.

- Credit Buyers: Often large companies that have their own emission-reduction targets. When they’ve done all they can internally but still need to meet their goals, they can purchase credits from producers.

The money buyers pay goes back to producers as compensation for their reduction efforts. Through this circulation of funds, the scheme aims to balance environmental benefits with economic viability.


## Methodology [AG005](https://japancredit.go.jp/pdf/methodology/AG-005_v3.0.pdf): Mid-Season Drainage Extension

### Key Requirement
- Extend the mid-season drainage period by at least 7 days compared to the average drainage period over the past two years.
- The extra days can be added either before or after the conventional drainage window.

### How much methane is reduced?

1. Determine the methane emission factor for your field (this varies by region, soil type, etc.).
2. Apply a 30% reduction to that factor, reflecting the suppression of methane generation shown by research.
3. Calculate the emissions difference over your field’s planted area (e.g., per hectare) to find the total CO₂-equivalent reduction.

The calculation steps, based on the simplified model, are as follows:

**1. Input Parameters**
*   _area\_ha_: Paddy field area (ha)
*   _prefecture_: Prefecture name
*   _drainage\_class_: Drainage class of the soil
*   _straw\_removal\_kg\_10a_: Amount of straw removed (kg/10a)
*   _compost\_rate_: Rate of compost application (fixed at 0.5 in the current model)

**2. Determine Region and Coefficients**
$$
region = \text{PREF\_TO\_REGION}[prefecture]
$$
$$
key = region + drainage\_class
$$
$$
coeffs = \text{COEFF}[key]
$$

**3. Calculate Straw Incorporation Rate**
$$
straw\_prod = \text{PREF\_TO\_STRAW}[prefecture]
$$
$$
incorporation\_percent = \max(0, \min(90, 100 \times (1 - \frac{straw\_removal\_kg\_10a}{straw\_prod})))
$$
$$
incorporation\_rate = \frac{incorporation\_percent}{90}
$$

**4. Calculate Adjusted Emission Coefficient**
$$
straw\_coeff = coeffs[\text{"straw"}]
$$
$$
manure\_coeff = coeffs[\text{"manure"}]
$$
$$
no\_straw\_coeff = coeffs[\text{"no\_straw"}]
$$
$$
coeff\_val = \min(\max(straw\_coeff, manure\_coeff), no\_straw\_coeff + (straw\_coeff - no\_straw\_coeff) \times incorporation\_rate + (manure\_coeff - no\_straw\_coeff) \times compost\_rate)
$$

**5. Calculate Emissions**
$$
GWP_{CH4} = 28
$$
$$
conv\_factor = \frac{16}{12} \times GWP_{CH4} \times 10^{-3}
$$
$$
coeff_{baseline} = coeff\_val
$$
$$
coeff_{project} = coeff\_val \times 0.7　(30\% reduction)
$$
$$
baseline\_emission = area\_ha \times coeff_{baseline} \times conv\_factor \quad [\text{tCO}_2\text{e}]
$$
$$
project\_emission = area\_ha \times coeff_{project} \times conv\_factor \quad [\text{tCO}_2\text{e}]
$$

**6. Calculate Emission Reduction**
$$
emission\_reduction_{tCO2} = \text{floor}(baseline\_emission - project\_emission) \quad [\text{tCO}_2\text{e}]
$$

This model is a simplified interpretation based on the J-Credit Scheme methodology AG-005. For detailed parameters and coefficients, please refer to [`rice_ch4_params.py`](https://github.com/seima-osako/rice-ch4-simulator/blob/main/rice_ch4_params.py).
