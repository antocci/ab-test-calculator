import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons
from scipy import stats

def plot_interactive_alpha_beta():
    # Initial Parameters
    init_n = 30
    init_alpha = 0.05
    init_effect = 2.5  # Distance between H0 and H1 peaks
    
    # Create the figure
    fig, ax = plt.subplots(figsize=(12, 7))
    plt.subplots_adjust(left=0.1, bottom=0.35, right=0.9, top=0.9)
    
    # X-axis range
    x = np.linspace(-4, 8, 1000)
    
    # Elements to be updated (Updated labels)
    line_h0, = ax.plot(x, np.zeros_like(x), label='Noise (H0)', color='blue', lw=2)
    line_h1, = ax.plot(x, np.zeros_like(x), label='Real Effect (H1)', color='orange', lw=2)
    
    # Critical lines (Right and Left)
    crit_line_r = ax.axvline(x=0, color='red', linestyle='--', label='Threshold (+)')
    crit_line_l = ax.axvline(x=0, color='red', linestyle='--', alpha=0, label='Threshold (-)') # Hidden by default
    
    fill_alpha_r = ax.fill_between(x, 0, 0, color='red', alpha=0.3)
    fill_alpha_l = ax.fill_between(x, 0, 0, color='red', alpha=0.3)
    fill_beta = ax.fill_between(x, 0, 0, color='gray', alpha=0.3)
    # Add fill for Power (Green)
    fill_power = ax.fill_between(x, 0, 0, color='green', alpha=0.2)
    
    # Text annotations - fixed positions relative to axes or dynamic
    txt_alpha = ax.text(0.95, 0.80, '', transform=ax.transAxes, color='red', fontsize=10, ha='right')
    txt_beta = ax.text(0.05, 0.80, '', transform=ax.transAxes, color='gray', fontsize=10, ha='left')
    txt_power = ax.text(0.05, 0.75, '', transform=ax.transAxes, color='green', fontsize=10, ha='left')
    title_text = ax.text(0.5, 1.05, '', transform=ax.transAxes, ha='center', fontsize=12, fontweight='bold')

    ax.set_ylim(0, 0.55)
    ax.set_xlim(-4, 8)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize='small')
    ax.grid(True, alpha=0.2)
    
    # Add static helper labels on the plot
    ax.text(0, 0.02, "Safe Zone\n(Keep H0)", color='blue', alpha=0.5, ha='center', fontsize=9)
    ax.text(5, 0.02, "Success Zone\n(Reject H0)", color='green', alpha=0.5, ha='center', fontsize=9)

    # Sliders axes
    ax_n = plt.axes([0.15, 0.25, 0.65, 0.03])
    ax_alpha = plt.axes([0.15, 0.20, 0.65, 0.03])
    ax_eff = plt.axes([0.15, 0.15, 0.65, 0.03])
    
    # Sliders
    s_n = Slider(ax_n, 'Sample Size (N)', 2, 1000, valinit=init_n, valstep=1)
    s_alpha = Slider(ax_alpha, 'Alpha (False Alarm)', 0.01, 0.20, valinit=init_alpha, valstep=0.001)
    s_eff = Slider(ax_eff, 'Effect Size (Signal)', 0.0, 5.0, valinit=init_effect)
    
    # Radio buttons for distribution type
    ax_radio_dist = plt.axes([0.85, 0.15, 0.12, 0.12])
    radio_dist = RadioButtons(ax_radio_dist, ('T-Dist', 'Z-Dist'))

    # Radio buttons for Test Type (Sides)
    ax_radio_sides = plt.axes([0.85, 0.02, 0.12, 0.12])
    radio_sides = RadioButtons(ax_radio_sides, ('1-Sided', '2-Sided'))

    def update(val):
        n = int(s_n.val)
        alpha = s_alpha.val
        effect = s_eff.val
        dist_type = radio_dist.value_selected
        sides_type = radio_sides.value_selected
        
        is_two_sided = (sides_type == '2-Sided')

        # Determine distribution
        if dist_type == 'Z-Dist':
            dist = stats.norm
            dist_name = "Z (Normal)"
        else:
            df = max(1, n - 1)
            dist = stats.t(df)
            dist_name = f"T (Student, df={df})"

        # Critical Value Calculations
        if is_two_sided:
            # Split alpha into two tails
            crit_val = dist.ppf(1 - alpha / 2)
            crit_val_l = -crit_val
            alpha_label = f"Alpha/2: {alpha/2:.1%}"
        else:
            # One tail
            crit_val = dist.ppf(1 - alpha)
            crit_val_l = -999 # Far away
            alpha_label = f"Alpha: {alpha:.1%}"
        
        # H0 & H1 PDFs
        y_h0 = dist.pdf(x)
        y_h1 = dist.pdf(x - effect)
        
        # Update lines
        line_h0.set_ydata(y_h0)
        line_h1.set_ydata(y_h1)
        
        crit_line_r.set_xdata([crit_val, crit_val])
        
        if is_two_sided:
            crit_line_l.set_xdata([crit_val_l, crit_val_l])
            crit_line_l.set_alpha(1) # Show it
        else:
            crit_line_l.set_alpha(0) # Hide it
        
        # Calculates Areas/Fills
        nonlocal fill_alpha_r, fill_alpha_l, fill_beta, fill_power
        fill_alpha_r.remove()
        fill_alpha_l.remove()
        fill_beta.remove()
        fill_power.remove()
        
        # 1. Alpha Right (False Positive)
        mask_alpha_r = x >= crit_val
        fill_alpha_r = ax.fill_between(x, 0, y_h0, where=mask_alpha_r, color='red', alpha=0.5, label='Alpha R')
        
        # 2. Alpha Left (False Positive - Only for 2-sided)
        if is_two_sided:
            mask_alpha_l = x <= crit_val_l
            fill_alpha_l = ax.fill_between(x, 0, y_h0, where=mask_alpha_l, color='red', alpha=0.5, label='Alpha L')
        else:
            # Create empty fill
            fill_alpha_l = ax.fill_between(x, 0, 0, color='red', alpha=0.0)

        # 3. Beta (Missed): H1 falls in the "Safe Zone" (Acceptance Region)
        # Safe zone is everything between left_crit and right_crit.
        # For 1-sided, left_crit is effectively -infinity.
        if is_two_sided:
            mask_beta = (x > crit_val_l) & (x < crit_val)
        else:
            mask_beta = x < crit_val
            
        fill_beta = ax.fill_between(x, 0, y_h1, where=mask_beta, color='gray', alpha=0.5, label='Beta')
        
        # 4. Power (Success): H1 falls in Rejection Regions
        if is_two_sided:
            mask_power = (x <= crit_val_l) | (x >= crit_val)
        else:
            mask_power = x >= crit_val
            
        fill_power = ax.fill_between(x, 0, y_h1, where=mask_power, color='green', alpha=0.3, label='Power')

        # Calculate logical values
        if is_two_sided:
            # Power = P(reject) = P(X > crit) + P(X < -crit) | H1
            # Usually P(X < -crit) is negligible for positive effect size, but formally exists.
            beta_prob = dist.cdf(crit_val - effect) - dist.cdf(crit_val_l - effect)
        else:
            beta_prob = dist.cdf(crit_val - effect)
            
        power_prob = 1 - beta_prob
        
        # Update Texts
        txt_alpha.set_text(f"{alpha_label}\nThreshold: ±{crit_val:.2f}" if is_two_sided else f"{alpha_label}\nThreshold: {crit_val:.2f}")
        txt_beta.set_text(f"Beta (Missed): {beta_prob:.1%}")
        txt_power.set_text(f"Power (Success): {power_prob:.1%}")
        
        side_text = "2-Sided" if is_two_sided else "1-Sided"
        title_text.set_text(f"{dist_name} | {side_text} | N={n}")
        
        fig.canvas.draw_idle()

    s_n.on_changed(update)
    s_alpha.on_changed(update)
    s_eff.on_changed(update)
    radio_dist.on_clicked(update)
    radio_sides.on_clicked(update)
    
    # Run first update
    update(None)
    
    plt.show()

if __name__ == "__main__":
    print("Opening interactive visualization...")
    print("Controls:")
    print("1. Alpha Slider: Change the 'Strictness' of the test.")
    print("   -> Watch how moving the RED line creates more GREY area (Beta).")
    print("2. N Solver: Change Sample Size.")
    print("   -> Watch how T-distribution gets sharper (like Z) and tails get thinner.")
    print("3. Effect Size: Move the orange hill.")
    print("   -> Distant hills are easier to distinguish.")
    
    try:
        plot_interactive_alpha_beta()
    except KeyboardInterrupt:
        print("\nClosed.")
