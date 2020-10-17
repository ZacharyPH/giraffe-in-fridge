jQuery(document).ready(function($) {

	$('#featured_items').slick({
		draggable: true,
	    arrows: true,
	    dots: false,
	    fade: true,
	    speed: 900,
	    infinite: true,
	    cssEase: 'cubic-bezier(0.7, 0, 0.3, 1)',
	    touchThreshold: 100,
	    autoplay: true,
	    autoplaySpeed: 5000
	});

});