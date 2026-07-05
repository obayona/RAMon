// components/WelcomeScreen.tsx
export const WelcomeScreen = () => {
   return (
      <div className='h-full flex flex-col items-center justify-center text-center text-gray-500'>
         <h2 className='text-xl font-semibold text-gray-800'>
            👋 Bienvenido al chat
         </h2>
         <p className='mt-2 max-w-md'>
            Escribe un mensaje para empezar la conversación.
         </p>
      </div>
   );
};
