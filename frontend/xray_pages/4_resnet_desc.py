import streamlit as st

st.markdown(
    """ 
> We used the ResNet50 architecture as the backbone of our classification models. ResNet50 is a deep convolutional neural network with 50 layers,
> originally introduced by He et al. in 2015. It is well known for its residual connections, which allow the neural network to learn identity mappings
> via skip connections, and helps by doing so mitigating the vanishing gradient problem. The ResNet50 framework allows gradients to flow more directly
> across layers, so a training of very deep architectures is enabled. ResNet50 has been pretrained on the ImageNet dataset, making it a strong candidate
> for transfer learning tasks in medical imaging, where annotated data is often limited.
> Although the name "ResNet50" refers to 50 convolutional and fully connected layers with trainable parameters, the actual model in Keras consists of
> more than 170 layers. This is because operations such as activations, batch normalizations, and residual additions are represented as individual
> layers. For fine-tuning purposes, we typically focus on trainable convolutional layers rather than counting all layers indiscriminately.
<br> 

<table style="border:3px solid black; border-radius:6px; background:#f9f9f9; 
             padding:10px; border-collapse:collapse; width:100%;">
  <tr><td>
    <strong>Note on ‘vanishing gradient problem’</strong><br>
    <small>
      In machine learning, the vanishing gradient problem is the problem of greatly diverging gradient magnitudes 
      between earlier and later layers encountered when training neural networks with backpropagation. In such methods 
      neural network weights are updated proportional to their partial derivative of the loss function. As the number of 
      forward propagation steps in a network increases, for instance due to greater network depth, the gradients of 
      earlier weights are calculated with increasingly many multiplications. These multiplications shrink the gradient 
      magnitude. Consequently, the gradients of earlier weights will be exponentially smaller than the gradients of later 
      weights. This difference in gradient magnitude might introduce instability in the training process, slow it, or 
      halt it entirely. For instance, consider the hyperbolic tangent activation function. The gradients of this function 
      are in range [−1,1]. The product of repeated multiplication with such gradients decreases exponentially. The 
      inverse problem, when weight gradients at earlier layers get exponentially larger, is called the exploding gradient 
      problem.
      <a href="https://en.wikipedia.org/wiki/Vanishing_gradient_problem">Source</a>
    </small>
  </td></tr>
</table>
""",
    unsafe_allow_html=True,
)

st.markdown(""" 


""")
